# Copyright (C) 2020-2021 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Landmarks Shard Descriptor."""

import json
import os
import shutil
from hashlib import md5
from logging import getLogger
from pathlib import Path
from random import shuffle
from zipfile import ZipFile

import numpy as np
import pandas as pd
from kaggle.api.kaggle_api_extended import KaggleApi

from openfl.interface.interactive_api.shard_descriptor import ShardDataset
from openfl.interface.interactive_api.shard_descriptor import ShardDescriptor

logger = getLogger(__name__)


class LandmarkShardDataset(ShardDataset):
    """Landmark Shard dataset class."""

    def __init__(self, dataset_dir: Path,
                 rank: int = 1, worldsize: int = 1):
        """Initialize LandmarkShardDataset."""
        self.rank = rank
        self.worldsize = worldsize
        self.dataset_dir = dataset_dir
        self.img_names = list(self.dataset_dir.glob('img_*.npy'))

        # Sharding
        self.img_names = self.img_names[self.rank - 1::self.worldsize]
        # Shuffling the results dataset after choose half pictures of each class
        shuffle(self.img_names)

    def __getitem__(self, index):
        """Return a item by the index."""
        # Get name key points file
        # f.e. image name:  'img_123.npy, corresponding name of the key points: 'keypoints_123.npy'
        kp_name = str(self.img_names[index]).replace('img', 'keypoints')
        return np.load(self.img_names[index]), np.load(self.dataset_dir / kp_name)

    def __len__(self):
        """Return the len of the dataset."""
        return len(self.img_names)


class LandmarkShardDescriptor(ShardDescriptor):
    """Landmark Shard descriptor class."""

    def __init__(self, data_folder: str = 'data',
                 rank_worldsize: str = '1, 1',
                 **kwargs):
        """Initialize LandmarkShardDescriptor."""
        super().__init__()
        # Settings for sharding the dataset
        self.rank, self.worldsize = map(int, rank_worldsize.split(','))

        self.data_folder = Path.cwd() / data_folder
        self.download_data()

        # Calculating data and target shapes
        ds = self.get_dataset()
        sample, target = ds[0]
        self._sample_shape = [str(dim) for dim in sample.shape]
        self._target_shape = str(len(target.shape))

        assert self._target_shape == '1', 'Target shape Error'

    def process_data(self, name_csv_file):
        """Process data from csv to numpy format and save it in the same folder."""
        data_df = pd.read_csv(self.data_folder / name_csv_file)
        data_df.fillna(method='ffill', inplace=True)
        keypoints = data_df.drop('Image', axis=1)
        cur_folder = str(self.data_folder.relative_to(Path.cwd())) + '/'

        for i in range(data_df.shape[0]):
            img = data_df['Image'][i].split(' ')
            img = np.array(['0' if x == '' else x for x in img], dtype='float32').reshape(96, 96)
            np.save(cur_folder + 'img_' + str(i) + '.npy', img)
            y = np.array(keypoints.iloc[i, :], dtype='float32')
            np.save(cur_folder + 'keypoints_' + str(i) + '.npy', y)

    def download_data(self):
        """Download dataset from Kaggle."""
        if not os.path.exists(self.data_folder):
            os.mkdir(self.data_folder)

        if not self.is_dataset_complete():
            logger.info('Your dataset is absent or damaged. Downloading ... ')
            api = KaggleApi()
            api.authenticate()

            if os.path.exists('data/train'):
                shutil.rmtree('data/train')

            api.competition_download_file(
                'facial-keypoints-detection',
                'training.zip', path=self.data_folder
            )

            with ZipFile(self.data_folder / 'training.zip', 'r') as zipobj:
                zipobj.extractall(self.data_folder)

            os.remove(self.data_folder / 'training.zip')

            self.process_data('training.csv')
            os.remove(self.data_folder / 'training.csv')
            self.save_all_md5()

    def get_dataset(self, dataset_type='train'):
        """Return a shard dataset by type."""
        return LandmarkShardDataset(
            dataset_dir=self.data_folder,
            rank=self.rank,
            worldsize=self.worldsize
        )

    def calc_all_md5(self):
        """Calculate hash of all dataset."""
        md5_dict = {}
        for root, _, files in os.walk(self.data_folder):
            for file in files:
                if file == 'dataset.json':
                    continue
                md5_calc = md5()
                rel_dir = os.path.relpath(root, self.data_folder)
                rel_file = os.path.join(rel_dir, file)

                with open(self.data_folder / rel_file, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b''):
                        md5_calc.update(chunk)
                    md5_dict[rel_file] = md5_calc.hexdigest()
        return md5_dict

    def save_all_md5(self):
        """Save dataset hash."""
        all_md5 = self.calc_all_md5()
        with open(os.path.join(self.data_folder, 'dataset.json'), 'w') as f:
            json.dump(all_md5, f)

    def is_dataset_complete(self):
        """Check dataset integrity."""
        new_md5 = self.calc_all_md5()
        try:
            with open(os.path.join(self.data_folder, 'dataset.json'), 'r') as f:
                old_md5 = json.load(f)
        except FileNotFoundError:
            return False

        return new_md5 == old_md5

    @property
    def sample_shape(self):
        """Return the sample shape info."""
        return self._sample_shape

    @property
    def target_shape(self):
        """Return the target shape info."""
        return self._target_shape

    @property
    def dataset_description(self) -> str:
        """Return the dataset description."""
        return (f'Dogs and Cats dataset, shard number {self.rank} '
                f'out of {self.worldsize}')