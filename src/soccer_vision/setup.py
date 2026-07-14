from setuptools import find_packages, setup

package_name = 'soccer_vision'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'opencv-python'],
    zip_safe=True,
    maintainer='sharmin',
    maintainer_email='sharmin@todo.todo',
    description='Computer vision node for detecting soccer balls',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'ball_tracker = soccer_vision.ball_tracker_node:main',
            'camera_hub = soccer_vision.camera_hub_node:main',
            'lidar_hub = soccer_vision.lidar_hub_node:main'
        ],
    },
)
