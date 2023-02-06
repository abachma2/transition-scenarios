import numpy as np
import sys
import os
from random import uniform
sys.path.append('../../../../../scripts')
import dakota_input as inp

f = open("fine_tuning.csv", 'w')

counter = 40
for m_type in ['replace_uniform', 'offset_normal']:
    for pop_size in [25, 50]:
        for c_penalty in range(5):         
            variable_dict = {'pop_size':pop_size,
                            'mutation_type':m_type,
                            'mutation_rate':np.round(uniform(0.025, 0.19),3),
                            'crossover_rate':np.round(uniform(0.3, 0.9),3),
                            'constraint':np.round(uniform(1, 2),3),
                            'counter':counter}
            dakota_file = f"tuning_{counter}.in"
            inp.render_input("soga_tuning_template.in", variable_dict, dakota_file)

            f.write(m_type + "," + str(pop_size) + "," +
                    str(variable_dict['mutation_rate']) + "," + 
                    str(variable_dict['crossover_rate']) + "," +
                    str(variable_dict['constraint']) + ", \n") 
            counter += 1
