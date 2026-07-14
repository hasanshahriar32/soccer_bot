from setuptools import find_packages, setup

package_name = 'soccer_navigation'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sharmin',
    maintainer_email='sharmin@todo.todo',
    description='Lidar-based obstacle avoidance and navigation for soccer bot',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'obstacle_avoidance = soccer_navigation.obstacle_avoidance_node:main'
        ],
    },
)
