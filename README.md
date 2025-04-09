# Alchemist-Project-Creator
This is a small tool to quickly create a project file for Alchemist by Scobalula

# Requirements to Install from Source
pip install PyQt5
pip install qtmodern


# General Breakdown
Currently this is only set up for the base stuff. Anything that needs adding let me know and ill add it asap. 

Drag in the idle, pose_l,pose_r & the skeleton at the top. 

The bottom 2 boxes are for animations.
Left = Additives, Gesture/GesturePose
Right = Normal Animations

# Adding to the mapping editor
This is an example:
Key                                 Values:
walk_offset_additive,walk_to_sprint sprint_in,1,1

The first 2 keys are the names of the additive in the file: for example:
vm_p08_sn_ultiger_walk_offset_additive,vm_p08_sn_ultiger_walk_to_sprint

The second set of values is the name of the output file:
so because the top uses a walk_to_sprint ive decided this file should be:
vm_p08_sn_ultiger_sprint_in

the 1,1 is the type of animation:

0 = Normal Animation
1 = Additive Animation
2 = Gesture Animation
3 = GesturePose Animation

So the top 2 examples: walk_offset_additive,walk_to_sprint both use 1 for additive. 
