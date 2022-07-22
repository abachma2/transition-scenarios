import unittest
import numpy as np
import pandas as pd
import math
from pandas._testing import assert_frame_equal
from pandas._testing import assert_series_equal
import sys

sys.path.insert(0, '../')
import output_metrics as oup

class Test_static_info(unittest.TestCase):
    def setUp(self):
        '''
        This defines the output files and a test DataFrame to use within the
        test suite.

        The first output file (transition_metrics_decommission_test.sqlite)
        models Reactor_type1 and Reactor_type2 prototypes with a lifetime of
        2 timesteps. This ensures that all of these prototypes will be
        decommissioned in the simulation.

        The second output file (transition_metrics_nodecommission_test.sqlite)
        models Reactor_type1 and Reactor_type2 prototypes with a lifetime of
        10 timesteps. This ensures that they are not decommissioned during the
        simualtion.

        Both output files model a 7-month fuel cycle with the reactor
        prototypes with manually defined deployment through a
        cycamore::DeployInst. 1 Reactor_type1 is built at timestep 1, 1
        Reactor_type2 is built at both timestep 2 and 3.
        '''
        self.output_file1 = 'transition_metrics_decommission_test.sqlite'
        self.output_file2 = 'transition_metrics_nodecommission_test.sqlite'
        self.test_df1 = pd.DataFrame(
            data={
                'Time': [
                    0, 1, 1, 3], 'Quantity': [
                    2, 5, 6, 8], 'Commodity': [
                    'fresh_uox', 'spent_uox', 'fresh_uox', 'fresh_uox'],
                'Prototype': ['FuelCycle', 'LWR', 'Reactor_type1', 'LWR']})
        self.test_df2 = pd.DataFrame(
            data={
                'Time': [
                    0, 2, 3, 3, 5], 'Quantity': [
                    2, 5, 6, 8, 2], 'Commodity': [
                    'fresh_uox', 'spent_uox', 'fresh_uox', 'fresh_uox', 'spent_uox'],
                'Prototype': [
                'FuelCycle', 'LWR', 'Reactor_type1', 'LWR', 'Reactor_type1']})
        self.test_df3 = pd.DataFrame(
            data={
                'Time': [
                    0, 2, 3, 3, 5], 'Quantity': [
                    2, 5, 6, 8, float('NaN')], 'Commodity': [
                    'fresh_uox', 'spent_uox', 'fresh_uox', 'fresh_uox', 'spent_uox'],
                'Prototype': [
                    'FuelCycle', 'LWR', 'Reactor_type1', 'LWR', 'Reactor_type1']})
        self.assays = {'Reactor_type1': 0.10, 'Reactor_type2': 0.045,
                       'tails': 0.002, 'feed': 0.00711}
        self.wastes = {'Reactor_type1': 'waste', 'Reactor_type2': 'spent_uox',
                       'Reactor_type3': 'spent_uox', 'Reactor_type4': 'waste'}

    def test_merge_and_fillna_col1(self):
        '''
        Tests the function with the two default arguments supplied when the left
        DataFrame does not contain a NaN value.
        '''
        exp = pd.DataFrame(data={
            'Time': [
                0, 1, 1, 3], 'Quantity': [
                2, 5, 6, 8], 'Commodity': [
                'fresh_uox', 'spent_uox', 'fresh_uox', 'fresh_uox'],
            'Prototype': ['FuelCycle', 'LWR', 'Reactor_type1', 'LWR']})
        obs = oup.merge_and_fillna_col(
            self.test_df1, self.test_df2, 'Quantity', 'Prototype')
        assert_frame_equal(exp, obs)

    def test_merge_and_fillna_col2(self):
        '''
        Tests the function with the two default arguments supplied when the left
        DataFrame does contain a NaN value.
        '''
        exp = pd.DataFrame(data={
            'Time': [
                0, 2, 3, 3, 5], 'Quantity': [
                2.0, 5.0, 6.0, 8.0, 'Reactor_type1'], 'Commodity': [
                'fresh_uox', 'spent_uox', 'fresh_uox', 'fresh_uox', 'spent_uox'],
            'Prototype': ['FuelCycle', 'LWR', 'Reactor_type1', 'LWR', 'Reactor_type1']})
        obs = oup.merge_and_fillna_col(
            self.test_df3, self.test_df2, 'Quantity', 'Prototype')
        assert_frame_equal(exp, obs)

    def test_merge_and_fillna_col3(self):
        '''
        Tests the function with the default argument fpr how, but specifying
        a column to merge on when the left DataFrame does not contain a NaN 
        value. 
        '''
        exp = pd.DataFrame(data={
            'Time': [
                0, 1, 1, 3], 'Quantity': [
                2, 5, 6, 8], 'Commodity': [
                'fresh_uox', 'spent_uox', 'fresh_uox', 'fresh_uox'],
            'Prototype': ['FuelCycle', 'LWR', 'Reactor_type1', 'LWR']})
        mergeon = ['Time', 'Quantity', 'Commodity', 'Prototype']
        obs = oup.merge_and_fillna_col(
            self.test_df1,
            self.test_df2,
            'Quantity',
            'Prototype',
            on=mergeon)
        assert_frame_equal(exp, obs)

    def test_merge_and_fillna_col4(self):
        '''
        Tests the function with the default for how it is used when an argument
        is given for when the left DataFrame contains a NaN value. 
        '''
        exp = pd.DataFrame(data={
            'Time': [
                0, 2, 3, 3, 5], 'Quantity': [
                2.0, 5.0, 6.0, 8.0, 'Reactor_type1'], 'Commodity': [
                'fresh_uox', 'spent_uox', 'fresh_uox', 'fresh_uox', 'spent_uox'],
            'Prototype': ['FuelCycle', 'LWR', 'Reactor_type1', 'LWR', 'Reactor_type1']})
        mergeon = ['Time', 'Quantity', 'Commodity', 'Prototype']
        obs = oup.merge_and_fillna_col(
            self.test_df3,
            self.test_df2,
            'Quantity',
            'Prototype',
            on=mergeon)
        assert_frame_equal(exp, obs)

    def test_get_table_from_output1(self):
        '''
        Test function for the AgentEntry table from self.output_file1.
        '''
        exp = pd.DataFrame(data={
            'AgentId': [19, 20, 21, 22],
            'Kind': ['Region', 'Inst', 'Facility', 'Facility'],
            'Spec': [':agents:NullRegion', ':agents:NullInst', ':cycamore:Source', ':cycamore:Sink'],
            'Prototype': ['United States', 'FuelCycle', 'FuelSupply', 'Repository'],
            'ParentId': [-1, 19, 20, 20],
            'Lifetime': [-1, -1, -1, -1],
            'EnterTime': [0, 0, 0, 0]
        })
        obs = oup.get_table_from_output(self.output_file1, 'AgentEntry')
        assert_frame_equal(exp, obs.drop('SimId', axis=1)[0:4])

    def test_get_table_from_output2(self):
        '''
        Test function for the Resource table from self.output_file1.
        '''
        exp = pd.DataFrame(data={
            'ResourceId': [10, 12, 14, 15],
            'ObjId': [9, 10, 11, 9],
            'TimeCreated': [1, 1, 1, 2],
            'Quantity': [33000.0, 33000.0, 33000.0, 33000.0],
            'Units': ['kg', 'kg', 'kg', 'kg']
        })
        obs = oup.get_table_from_output(self.output_file1, 'Resources')
        assert_frame_equal(exp, obs.drop('SimId', axis=1)[0:4])

    def test_create_agents_table1(self):
        '''
        Test the creation of the Agents DataFrame from output_file1, in
        which agents are decommissioned.
        '''
        exp = pd.DataFrame(data={
            'AgentId': [19, 20, 21, 22],
            'Kind': ['Region', 'Inst', 'Facility', 'Facility'],
            'Spec': [':agents:NullRegion', ':agents:NullInst', ':cycamore:Source', ':cycamore:Sink'],
            'Prototype': ['United States', 'FuelCycle', 'FuelSupply', 'Repository'],
            'ParentId': [-1, 19, 20, 20],
            'Lifetime': [-1, -1, -1, -1],
            'EnterTime': [0, 0, 0, 0],
            'ExitTime': [7.0, 7.0, 7.0, 7.0]
        })
        obs = oup.create_agents_table(self.output_file1)
        assert_frame_equal(exp, obs.drop('SimId', axis=1)[0:4])

    def test_create_agents_table2(self):
        '''
        Test correct creation of the Agents DataFrame from output_file2, in
        which agents are not decommissioned.
        '''
        exp = pd.DataFrame(data={
            'AgentId': [19, 20, 21, 22],
            'Kind': ['Region', 'Inst', 'Facility', 'Facility'],
            'Spec': [':agents:NullRegion', ':agents:NullInst', ':cycamore:Source', ':cycamore:Sink'],
            'Prototype': ['United States', 'FuelCycle', 'FuelSupply', 'Repository'],
            'ParentId': [-1, 19, 20, 20],
            'Lifetime': [-1, -1, -1, -1],
            'EnterTime': [0, 0, 0, 0],
            'ExitTime': [7.0, 7.0, 7.0, 7.0]
        })
        obs = oup.create_agents_table(self.output_file1)
        assert_frame_equal(exp, obs.drop('SimId', axis=1)[0:4])

    def test_merge_transactions_resources(self):
        '''
        Test merging the transactions and resources DataFrames with 
        output_file1.
        '''
        exp = pd.DataFrame(data={
            'TransactionId': [0, 1, 2, 3, 4],
            'SenderId': [21, 21, 21, 21, 21],
            'ReceiverId': [24, 24, 24, 24, 25],
            'ResourceId': [10, 12, 14, 26, 28],
            'Commodity': ['fresh_uox', 'fresh_uox', 'fresh_uox', 'fresh_uox', 'fresh_uox'],
            'Time': [1, 1, 1, 2, 2],
            'ObjId': [9, 10, 11, 21, 22],
            'Quantity': [33000.0, 33000.0, 33000.0, 33000.0, 3300.0],
            'Units': ['kg', 'kg', 'kg', 'kg', 'kg']
        })
        obs = oup.merge_transactions_resources(self.output_file1)
        assert_frame_equal(exp, obs.drop('SimId', axis=1)[0:5])

    def test_add_receiver_prototype(self):
        '''
        Test adding name of prototype receiving the commodity with 
        output_file1.
        '''
        exp = pd.DataFrame(data={
            'TransactionId': [0, 1, 2, 3, 4],
            'SenderId': [21, 21, 21, 21, 21],
            'ReceiverId': [24, 24, 24, 24, 25],
            'ResourceId': [10, 12, 14, 26, 28],
            'Commodity': ['fresh_uox', 'fresh_uox', 'fresh_uox', 'fresh_uox', 'fresh_uox'],
            'Time': [1, 1, 1, 2, 2],
            'ObjId': [9, 10, 11, 21, 22],
            'Quantity': [33000.0, 33000.0, 33000.0, 33000.0, 3300.0],
            'Units': ['kg', 'kg', 'kg', 'kg', 'kg'],
            'ReceiverPrototype': ['Reactor_type1', 'Reactor_type1', 'Reactor_type1', 'Reactor_type1', 'Reactor_type2']
        })
        obs = oup.add_receiver_prototype(self.output_file1)
        assert_frame_equal(exp, obs.drop('SimId', axis=1)[0:5])

    def test_add_sender_prototype(self):
        '''
        Test adding the prototype name sending the commodity with 
        output_file1.
        '''
        exp = pd.DataFrame(data={
            'TransactionId': [0, 1, 2, 3, 4],
            'SenderId': [21, 21, 21, 21, 21],
            'ReceiverId': [24, 24, 24, 24, 25],
            'ResourceId': [10, 12, 14, 26, 28],
            'Commodity': ['fresh_uox', 'fresh_uox', 'fresh_uox', 'fresh_uox', 'fresh_uox'],
            'Time': [1, 1, 1, 2, 2],
            'ObjId': [9, 10, 11, 21, 22],
            'Quantity': [33000.0, 33000.0, 33000.0, 33000.0, 3300.0],
            'Units': ['kg', 'kg', 'kg', 'kg', 'kg'],
            'SenderPrototype': ['FuelSupply', 'FuelSupply', 'FuelSupply', 'FuelSupply', 'FuelSupply']
        })
        obs = oup.add_sender_prototype(self.output_file1)
        assert_frame_equal(exp, obs.drop('SimId', axis=1)[0:5])

    def test_get_multiple_prototype_transactions1(self):
        '''
        Test function when commodity and prototype given are in the transactions
        dataframe, and the commodity is sent to the prototype.
        '''
        exp = pd.DataFrame(data={
            'Reactor_type1': [0.0, 99000.0, 33000.0, 0.0]
        })
        obs = oup.get_multiple_prototype_transactions(
            self.output_file1, ['Reactor_type1'], 'fresh_uox')
        assert_frame_equal(exp, obs[0:4])

    def test_get_multiple_prototype_transactions2(self):
        '''
        Test function when commodity and prototype given are in the transactions
        dataframe, and the commodity is not sent to the prototype.
        '''
        exp = pd.DataFrame(data={
            'Reactor_type1': [0.0, 0.0, 0.0, 0.0]
        })
        obs = oup.get_multiple_prototype_transactions(
            self.output_file1, ['Reactor_type1'], 'spent_uox')
        assert_frame_equal(exp, obs[0:4])

    def test_get_multiple_prototype_transactions3(self):
        '''
        Test function when commodity is in the transactions dataframe, but the
        prototype is not in the simulation.
        '''
        exp = pd.DataFrame(data={
            'Reactor_type3': [0.0, 0.0, 0.0, 0.0]
        })
        obs = oup.get_multiple_prototype_transactions(
            self.output_file1, ['Reactor_type3'], 'fresh_uox')
        assert_frame_equal(exp, obs[0:4])

    def test_get_multiple_prototype_transactions4(self):
        '''
        Test function when prototype is in the transactions dataframe, but the
        commodity is not in the simulation.
        '''
        exp = pd.DataFrame(data={
            'Reactor_type1': [0.0, 0.0, 0.0, 0.0]
        })
        obs = oup.get_multiple_prototype_transactions(
            self.output_file1, ['Reactor_type1'], 'u_ore')
        assert_frame_equal(exp, obs[0:4])

    def test_get_multiple_prototype_transactions5(self):
        '''
        Test function when multiple prototypes are listed, both prototypes and
        the commodity are in the transactions dataframe and the commodity is sent to
        both prototypes.
        '''
        exp = pd.DataFrame(data={
            'Reactor_type1': [0.0, 99000.0, 33000.0, 0.0],
            'Reactor_type2': [0.0, 0.0, 9900.0, 13200.0]
        })
        obs = oup.get_multiple_prototype_transactions(
            self.output_file1, ['Reactor_type1', 'Reactor_type2'], 'fresh_uox')
        assert_frame_equal(exp, obs[0:4])

    def test_get_enriched_u_mass1(self):
        '''
        Test with output_file1 for a single prototype that receives the 
        commodity specified.
        '''
        exp = 3300.0
        obs = oup.get_enriched_u_mass(self.output_file1, ['Reactor_type2'], 4)
        assert exp == obs

    def test_get_enriched_u_mass2(self):
        '''
        Test with output_file1 for two prototypes that receives the 
        commodity specified.
        '''
        exp = 59400.0
        obs = oup.get_enriched_u_mass(
            self.output_file1, [
                'Reactor_type1', 'Reactor_type2'], 2)
        assert exp == obs

    def test_calculate_swu1(self):
        '''
        Test for output_file1, the prototype specified receives enriched uranium after
        the transition start time.
        '''
        exp = 25378.59
        obs = oup.calculate_swu(
            self.output_file1,
            ['Reactor_type2'],
            4,
            self.assays)
        assert exp == obs

    def test_get_waste_discharged1(self):
        '''
        Test for output_file1 for a single prototype and a single commodity.
        The prototype discharges the specified commodity
        '''
        exp = 23100.0
        obs = oup.get_waste_discharged(
            self.output_file1, ['Reactor_type2'], 4, self.wastes)
        assert exp == obs

    def test_get_waste_discharged2(self):
        '''
        Test for output_file1 for a single prototype and a single commodity.
        The prototype does not discharge the specified commodity
        '''
        exp = 0.0
        obs = oup.get_waste_discharged(
            self.output_file1, ['Reactor_type1'], 4, self.wastes)
        assert exp == obs

    def test_get_waste_discharged3(self):
        '''
        Test for output_file1 with a single prototype and a single commodity.
        The protoype is not in the simulation but the commodity is.
        '''
        exp = 0.0
        obs = oup.get_waste_discharged(
            self.output_file1, ['Reactor_type3'], 4, self.wastes)
        assert exp == obs

    def test_get_waste_discharged4(self):
        '''
        Test for output_file1 with a single prototype and a single commodity,
        neither the prototype nor the commodity are in the simulation.
        '''
        exp = 0.0
        obs = oup.get_waste_discharged(
            self.output_file1, ['Reactor_type4'], 4, self.wastes)
        assert exp == obs

    def test_get_waste_discharged5(self):
        '''
        Test for output_file1 with a multiple prototypes in the simulation, but
        only one of the commodities is in the simulation.
        '''
        exp = 23100.0
        obs = oup.get_waste_discharged(
            self.output_file1, [
                'Reactor_type1', 'Reactor_type2'], 4, self.wastes)
        assert exp == obs
