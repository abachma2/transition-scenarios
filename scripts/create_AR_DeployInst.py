import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import xmltodict
from pprint import pprint
import math
import os
import sys


def convert_xml_to_dict(filename):
    '''
    Reads in an xml file and converts it to a python dictionary

    Parameters:
    -----------
    filename: str
        name of xml file

    Returns:
    --------
    xml_dict: dict of strings
        contents of the xml file as a dictionary

    '''
    xml_dict = xmltodict.parse(open(filename, 'r').read())
    return xml_dict


def get_deployinst_dict(
        deployinst_dict,
        power_dict,
        path="../input/haleu/inputs/united_states/reactors/"):
    '''
    Removes any non-power producing prototypes from the dictionary of
    the DeployInst. This also removes the 'val' level of information.
    Returns a dictionary about deployment information from the Inst.
    This function assumes the input for a single DeployInst is provided.
    Only the the prototype names that are in the power_dict are included
    in the output, so that only prototypes that produce power are considered.

    Parameters:
    -----------
    deployinst_dict: dict
        dictionary of DeployInst information. This dictionary is assumed
        to be nested, with the top key being 'DeployInst', the keys of
        the next level being 'prototypes', 'build_times', 'n_build',
        and optionally 'lifetimes'. Each of those rx_info  dictionaries are
        nested with key of 'val', and value of a list of the integer
        values.
    reactor_dict: dict
        dictionary of LWR prototype names. Keys are the names of each
        prototype for LWRs, with values of the rated power for the prototype.
    path: str
        path to xml files for each prototype

    Returns:
    --------
    deployed_dict: dict
        dictionary of information about LWR prototypes and
        their deployment. The keys are strs and values are lists of
        ints.
    '''
    deployed_dict = {}
    deployed_dict = {'lifetime': [],
                     'prototypes': [],
                     'n_build': [],
                     'build_times': []}
    for indx, val in enumerate(
            deployinst_dict['DeployInst']['prototypes']['val']):
        if val in power_dict.keys():
            if 'lifetimes' in deployinst_dict['DeployInst']:
                deployed_dict['lifetime'].append(int(
                    deployinst_dict['DeployInst']['lifetimes']['val'][indx]))
            else:
                deployed_dict['lifetime'].append(get_lifetime(path, val))
            deployed_dict['prototypes'].append(val)
            deployed_dict['n_build'].append(
                int(deployinst_dict['DeployInst']['n_build']['val'][indx]))
            deployed_dict['build_times'].append(
                int(deployinst_dict['DeployInst']['build_times']['val'][indx]))
    return deployed_dict


def get_powers(path):
    '''
    Read through each of the xml files in a given path to get the power
    output of each reactor facility. Getting this information from these
    files accounts for any capacity factors, which are not captured in
    the PRIS database.

    Parameters:
    -----------
    path: str
        directory name containing xml files for reactors

    Returns:
    --------
    rx_power: dict
        dictionary of reactor names and rated powers, the keys are the reactor
        names (strs), the values are their power outputs (ints). Any spaces
        in the keys are replaced with underscores.
    '''
    rx_power = {}
    for filename in os.listdir(path):
        file = os.path.join(path, filename)
        rx_info = convert_xml_to_dict(file)
        rx_power.update(
            {filename[:-4]: rx_info['facility']['config']['Reactor']['power_cap']})
    return rx_power


def get_lifetime(path, name):
    ''''
    Get the lifetime of a prototype from a modular file of the prototype
    definition

    Parameters:
    -----------
    path: str
        relative path to prototype definition file
    name: str
        name of prototype
    Returns:
    --------
    lifetime: int
        lifetime of prototype
    '''
    prototype_dict = convert_xml_to_dict(path + name + '.xml')
    lifetime = int(prototype_dict['facility']['lifetime'])
    return lifetime


def get_deployed_power(power_dict, deployed_dict, sim_duration):
    '''
    Creates array of the total power from agents in a given
    DeployInst. Each entry in the array is for each time step in
    the simulation.

    Parameters:
    -----------
    power_dict: dict
        contains the power output of each agent in the DeployInst.
        The keys are the reactor
        names (strs), the values are the rated powers (ints). Any spaces
        in the keys are replaced with underscores.
    deployed_dict: dict
        contains the lifetimes, number built, and name of each
        prototype in the DeployInst. The keys are strs and values
        are lists of ints.
    sim_duration: int
        number of timesteps in the simulation

    Returns:
    --------
    t: array of ints
        ranged arrays of durations
    inst_power: array of ints
        deployed power at each timestep from a single DeployInst
        based on the power and duration of each prototype
    '''
    t = np.arange(sim_duration)
    for key, val in deployed_dict.items():
        power_profile = np.zeros(len(t))
        for i, v in enumerate(deployed_dict['prototypes']):
            prototype_power = np.zeros(len(t))
            prototype_power[deployed_dict['build_times'][i]: deployed_dict['build_times'][
                i] + deployed_dict['lifetime'][i]] += \
                float(power_dict[v] * deployed_dict['n_build'][i])
            power_profile += prototype_power
    return t, power_profile


def determine_power_gap(power_profile, demand):
    '''
    Calculates the amount of power needed to be supplied
    based on the power produced and the demand equation

    Parameters:
    ----------
    power_profile: array of ints
        Amount of power produced at each time step
    demand: array of ints
        evaluated values of the power demand equation used

    Returns:
    --------
    power_gap: array of ints
        Amount of power needed to meet the power demand. Any negative
        values from an oversupply of power are changed to 0
    '''
    power_gap = demand - power_profile
    power_gap[power_gap < 0] = 0
    return power_gap


def determine_deployment_order(reactor_prototypes):
    '''
    Creates a list of the keys in reactor_prototypes ordering
    them in decreasing order of power

    Parameters:
    ----------
    reactor_prototypes: dict
        dictionary of information about prototypes in the form
        {name(str): (power(int), lifetime(int))}

    Returns:
    --------
    reactor_order: list of strs
        ordered list of reactor prototypes in decreasing order of
        power output.
    '''
    reactor_order = []
    keys = list(reactor_prototypes.keys())
    prototypes = reactor_prototypes.copy()
    for key in keys:
        max_power_prototype = max(prototypes,
                                  key=lambda x: prototypes[x][0])
        reactor_order.append(max_power_prototype)
        prototypes.pop(max_power_prototype, None)
    return reactor_order


def determine_deployment_schedule(
        power_gap,
        reactor_prototypes,
        prototype=None,
        share=0):
    '''
    Define the deployment schedule for one or more
    reactor prototypes based on a gap in production
    and demand. If multiple prototypes are provided, then
    they will be deployed in preferential order based on
    decreasing power output.

    Parameters:
    -----------
    power_gap: array
        gap in power production and demand
    reactor_prototypes: dictionary
        information about reactor prototypes to be deployed. The
        keys are the prototype names (strs) and the values are
        a tuple of the power output and lifetime (ints)
    prototype: str
        name of prototype to specify new market share of. If not
        indicated then prototypes in reactor_prototypes are
        deployed preferentially based on power output
    share: int
        percent of new build share to be occupied by specified
        prototype

    Returns:
    --------
    deploy_schedule: dict
        deployment schedule of reactor prototypes with the
        structure for a DeployInst
    '''
    deploy_schedule = {'DeployInst': {'prototypes': {'val': []},
                                      'build_times': {'val': []},
                                      'n_build': {'val': []},
                                      'lifetimes': {'val': []}}}
    reactors = determine_deployment_order(reactor_prototypes)
    if prototype is not None:
        reactors.remove(prototype)
    for index, value in enumerate(power_gap):
        if value <= 0:
            continue
        if prototype is not None:
            required_share = value * (share / 100)
            num_rxs = math.ceil(
                required_share /
                reactor_prototypes[prototype][0])
            power_gap[index:index + reactor_prototypes[prototype][1]] = \
                power_gap[index:index + reactor_prototypes[prototype]
                          [1]] - reactor_prototypes[prototype][0] * num_rxs
            value = value - reactor_prototypes[prototype][0] * num_rxs
            deploy_schedule['DeployInst']['prototypes']['val'].append(
                prototype)
            deploy_schedule['DeployInst']['n_build']['val'].append(num_rxs)
            deploy_schedule['DeployInst']['build_times']['val'].append(index)
            deploy_schedule['DeployInst']['lifetimes']['val'].append(
                reactor_prototypes[prototype][1])
        for reactor in reactors:
            if reactor == reactors[-1]:
                # for the last reactor round up to ensure gap is fully met, even if
                # power is slightly over supplied
                num_rxs = math.ceil(value / reactor_prototypes[reactor][0])
            else:
                num_rxs = math.floor(value / reactor_prototypes[reactor][0])
            if num_rxs <= 0:
                continue
            power_gap[index:index + reactor_prototypes[reactor][1]] = \
                power_gap[index:index + reactor_prototypes[reactor]
                          [1]] - reactor_prototypes[reactor][0] * num_rxs
            value = value - reactor_prototypes[reactor][0] * num_rxs
            deploy_schedule['DeployInst']['prototypes']['val'].append(reactor)
            deploy_schedule['DeployInst']['n_build']['val'].append(num_rxs)
            deploy_schedule['DeployInst']['build_times']['val'].append(index)
            deploy_schedule['DeployInst']['lifetimes']['val'].append(
                reactor_prototypes[reactor][1])

    return deploy_schedule

def deployment_schedule(       
        power_gap,
        reactor_prototypes,
        share={'Xe-100':0.2, 'MMR':0.2,'VOYGR':0.6}):
    '''
    Define the deployment schedule for one or more
    reactor prototypes based on a gap in production
    and demand. If multiple prototypes are provided, then
    they will be deployed in preferential order based on
    decreasing power output. This function is used to 
    specify a build share for all of the reactor 
    prototypes at once. 

    Parameters:
    -----------
    power_gap: array
        gap in power production and demand
    reactor_prototypes: dictionary
        information about reactor prototypes to be deployed. The
        keys are the prototype names (strs) and the values are
        a tuple of the power output and lifetime (ints)
    share: dictionary 
        define the build share for each prototype. The keys are 
        strings and the values are floats (percentage of share). 
   

    Returns:
    --------
    deploy_schedule: dict
        deployment schedule of reactor prototypes with the
        structure for a DeployInst
    '''
    deploy_schedule = {'DeployInst': {'prototypes': {'val': []},
                                      'build_times': {'val': []},
                                      'n_build': {'val': []},
                                      'lifetimes': {'val': []}}}
    reactors = reactor_prototypes.keys()
    for index, value in enumerate(power_gap):
        if value <= 0:
            continue
        num_rxs = share.copy()
        for reactor in reactors:
            required_share = value * (share[reactor])
            num_rxs[reactor] = math.ceil(
                required_share /
                reactor_prototypes[reactor][0]) 
        for key in num_rxs:  
            if num_rxs[key] <= 0:
                continue
            power_gap[index:index + reactor_prototypes[key][1]] = \
            power_gap[index:index + reactor_prototypes[key]
                        [1]] - reactor_prototypes[key][0] * num_rxs[key]
            
            deploy_schedule['DeployInst']['prototypes']['val'].append(
                    key)
            deploy_schedule['DeployInst']['n_build']['val'].append(num_rxs[key])
            deploy_schedule['DeployInst']['build_times']['val'].append(index)
            deploy_schedule['DeployInst']['lifetimes']['val'].append(
                    reactor_prototypes[key][1])
            value = value - reactor_prototypes[key][0] * num_rxs[key]

    return deploy_schedule


def write_deployinst(deploy_schedule, out_path):
    '''
    Write xml file for the DeployInst to meet the power demand

    Parameters:
    -----------
    deploy_schedule: dict
        deployment schedule of reactor prototypes, with
        the same schema as the DeployInst. Nest dictionary
        with the top key being 'DeployInst', next level of keys in
        'prototypes', 'n_build', 'build_times',  and 'lifetimes'. Each
        of those keys has a nested dictionary of {'val':[]}, with
        the values of that dictionary being a list.
    out_path: str
        path to where the file should be written

    Returns:
    --------
    null
        wites xml file for Cycamore DeployInst
    '''
    with open(out_path, 'w') as f:
        f.write(xmltodict.unparse(deploy_schedule, pretty=True))


def write_lwr_deployinst(lwr_param, DI_file, lwr_order):
    '''
    Create a DeployInst for the LWRs in the simulation using different
    lifetimes than what is defined from creating the DeployInst via
    scripts/create_cyclus_input.py. The first agent in the DeployInst
    is the SinkHLW, leading to the first lifetime item being 600
    time steps.

    Parameters:
    -----------
    lwr_param: float
        percent of LWRs to receive lifetime extensions
    DI_file: str
        file name and path to DeployInst file for LWRs to base information
        off of.
    lwr_order: str
        path and name of file containing LWRs ordered by power output.

    Returns:
    --------
    DI_dict: dict
        nested dictionary, contains information for the DeployInst in
        the form {'DeployInst':{'prototypes':{'val':[]}, 'n_build':
        {'val':[]}, 'build_times':{'val':[]},'lifetimes':{'val':[]}}}.
        The values in the inner-most dict are ints
    '''
    DI_dict = convert_xml_to_dict(DI_file)
    DI_dict['DeployInst']['lifetimes'] = {'val': []}
    DI_dict['DeployInst']['lifetimes']['val'] = np.repeat(720, 116)
    DI_dict['DeployInst']['lifetimes']['val'][0] = 600

    with open(lwr_order, 'r') as f:
        lwrs = f.readlines()
    for index, item in enumerate(lwrs):
        lwrs[index] = item.strip("\n")
    lwrs_extended = lwrs[:int(lwr_param) + 1]

    for lwr in lwrs_extended:
        index = DI_dict['DeployInst']['prototypes']['val'].index(lwr)
        DI_dict['DeployInst']['lifetimes']['val'][index] = 960
    return DI_dict


def write_AR_deployinst(
        lwr_DI,
        lwr_path,
        duration,
        reactor_prototypes,
        demand_eq,
        reactor=None,
        build_share=0):
    ''''
    Creates the DeployInst for deployment of advanced reactors.

    Parameters:
    -----------
    lwr_DI: dict
        dictionary of the DeployInst defining the deployment of LWRs
    lwr_path: str
        path to directory containing xml files defining each LWR in
        the simulation
    duration: int
        number of timesteps in the simulation
    reactor_prototypes: dict
        dictionary of information about prototypes in the form
        {name(str): (power(int), lifetime(int))}
    demand_eq: array
        energy demand at each time step in the simulation, length
        must match the value of duration
    reactor: str
        name of prototype of which to specify build share
    build_share: int
        percent of build share to apply for reactor


    Returns:
    --------
    deploy_schedule: dict
        nested dictionary, contains information for the DeployInst in
        the form {'DeployInst':{'prototypes':{'val':[]}, 'n_build':
        {'val':[]}, 'build_times':{'val':[]},'lifetimes':{'val':[]}}}.
        The values in the inner-most dict are ints
    '''
    lwr_powers = get_powers(lwr_path)
    deployed_lwr_dict = get_deployinst_dict(
        lwr_DI, lwr_powers, lwr_path)
    time, deployed_power = get_deployed_power(lwr_powers,
                                              deployed_lwr_dict,
                                              duration)
    power_gap = determine_power_gap(deployed_power, demand_eq)
    deploy_schedule = deployment_schedule(power_gap,
                                          reactor_prototypes)
    return deploy_schedule
