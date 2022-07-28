import sys
import os
from turtle import up
sys.path.append('../../../../../scripts')
import dakota_input as inp
import dakota_output as oup
# import output as oup
import dakota.interfacing as di
import subprocess
import create_AR_DeployInst as cdi
import numpy as np
# ----------------------------
# Parse Dakota parameters file
# ----------------------------

params, results = di.read_parameters_file()

# -------------------------------
# Convert and send to Cyclus
# -------------------------------

# Edit Cyclus input file
cyclus_template = 'xe-100_share_input.xml.in'
scenario_name = 'xe100_' + str(round(params['xe100']))
variable_dict = {'handle': scenario_name, 'xe100':str(int(params['xe100']))}
output_xml = './cyclus-files/xe100_share'+ str(params['xe100']) + '.xml'
inp.render_input(cyclus_template, variable_dict, output_xml)

# Create DeployInst for advanced reactors 
duration = 1500
reactor_prototypes = {'Xe-100':(76, 720), 'MMR':(5,240), 'VOYGR':(73, 720)}
demand_equation = np.zeros(duration)
demand_equation[721:] = 87198.156
deployinst = cdi.convert_xml_to_dict("../../../inputs/united_states/buildtimes/UNITED_STATES_OF_AMERICA/deployinst.xml")
lwr_powers = cdi.get_pris_powers('UNITED STATES OF AMERICA',"../../../../../database/", 2020)
deployed_lwr_dict = cdi.get_deployinst_dict(deployinst, lwr_powers, "../../../inputs/united_states/reactors/")
time, deployed_power = cdi.get_deployed_power(lwr_powers, deployed_lwr_dict, duration)
power_gap = cdi.determine_power_gap(deployed_power*0.9266, demand_equation)
deploy_schedule = cdi.determine_deployment_schedule(power_gap, reactor_prototypes, 'Xe-100',int(params['xe100']))
cdi.write_deployinst(deploy_schedule, "./cyclus-files/xe100_" + str(int(params['xe100'])) + "_deployinst.xml")

# Run Cyclus with edited input file
output_sqlite = './cyclus-files/' + scenario_name + '.sqlite'
os.system('rm ' + output_sqlite)
os.system('cyclus -i ' + output_xml + ' -o ' + output_sqlite + \
    ' --warn-limit 2')

# ----------------------------
# Return the results to Dakota
# ----------------------------
results['enr_u'].function = oup.get_enriched_u_mass(output_sqlite, 
                                                    ['Xe-100','MMR','VOYGR'],
                                                    721)
results['haleu'].function = oup.get_enriched_u_mass(output_sqlite, 
                                                    ['Xe-100','MMR'],
                                                    721)
results['swu'].function = oup.calculate_swu(output_sqlite, ['Xe-100','MMR','VOYGR'],
                                            721)
results['haleu_swu'].function = oup.calculate_swu(output_sqlite, ['Xe-100','MMR'],
                                            721)
results['waste'].function = oup.get_waste_discharged(output_sqlite, 
                                                    ['Xe-100','MMR','VOYGR'],
                                                    721,
                                                    {'MMR':'spent_MMR_haleu',
                                                    'Xe-100':'spent_xe100_haleu',
                                                    'VOYGR':'spent_smr_fuel'}
                                                    )
results['feed'].function = oup.calculate_feed(output_sqlite, 
                                             ['Xe-100','MMR'],
				             721)
			          
results.write()
