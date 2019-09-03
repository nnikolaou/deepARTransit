import os
import numpy as np
import tensorflow as tf
import matplotlib.pylab as plt
from deepartransit.models import deeparsys
from utils.config import get_config_file, process_config, split_grid_config
from utils.dirs import create_dirs
from utils.logger import Logger
from utils.argumenting import get_args
from utils.transit import get_transit_model
from deepartransit.data_handling import data_generator
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
import pandas as pd

if __name__ == '__main__':
    #config_path = os.path.join('deepartransit','experiments', 'deeparsys_dev','deeparsys_config.yml')
    try:
        args = get_args()
        print(args.experiment)
        if args.experiment:
            print('found an experiment argument:', args.experiment)
            meta_config_file = get_config_file(os.path.join("deepartransit", "experiments", args.experiment))
            print("which constains a config file", meta_config_file)
        else:
            meta_config_file = args.config
        print('processing the config from the config file')
        meta_config = process_config(meta_config_file)

    except:
        print("missing or invalid arguments")
        exit(0)
    grid_config = split_grid_config(meta_config)
    list_configs = [c for c in grid_config
                     if c['total_length'] == c['pretrans_length'] + c['trans_length'] + c['postrans_length']]

    df_scores = pd.DataFrame(index=list(range(len(list_configs))), columns=list(list_configs[0].keys())+['score'])
    print('Starting to run {} models'.format(len(list_configs)))
    for i, config in enumerate(list_configs):
        df_scores.loc[i, config.keys()] = list(config.values())
        print('model ',i)
        print(config)
        data = data_generator.DataGenerator(config)
        config = data.update_config()


        model = deeparsys.DeepARSysModel(config)

        model.delete_checkpoints()

        create_dirs([config.summary_dir, config.checkpoint_dir, config.plots_dir, config.output_dir])

        init = tf.global_variables_initializer()
        with tf.Session() as sess:
            sess.run(init)
            if not config.from_scratch:
                model.load(sess)
            logger = Logger(sess, config)

            transit_model = get_transit_model(config['transit_model'])
            print(transit_model)
            trainer = deeparsys.DeepARSysTrainer(sess, model, data, config, logger, transit_model)
            trainer.train(verbose=True)


            print(data.Z.shape, data.X.shape)
            samples = trainer.sample_sys_traces()
        print('best_Score', trainer.best_score)
        df_scores.loc[i,'score'] = trainer.best_score

        df_scores.to_csv(os.path.join("deepartransit", "experiments", config.exp_name, 'config_scores.csv'))
        # Saving output array
        #np.save(os.path.join(config.output_dir, 'pred_array.npy'), np.array(samples))
        #print('prediction sample of shape {} saved'.format(np.array(samples).shape))

