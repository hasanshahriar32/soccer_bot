import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'soccer_slam'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
        (os.path.join('share', package_name, 'maps'), glob('maps/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sharmin',
    maintainer_email='sharmin@todo.todo',
    description='Real-Time 2D LiDAR SLAM, Online Occupancy Mapping, and Spatial Coordinate Tracking Subsystem',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'coordinate_tracker = soccer_slam.coordinate_tracker:main',
            'slam_map_saver = soccer_slam.slam_map_saver:main',
        ],
    },
)
