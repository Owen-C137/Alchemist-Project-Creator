
## Disclaimer

This application was developed with ChatGPT


# Alchemist Project Creator

A small tool to quickly create a project file for Alchemist by Scobalula.

## Requirements

Before installing and running the tool, ensure you have the following packages installed:


- **pip install PyQt5**
- **pip install qtmodern**


## Overview

Currently, this tool is set up for the basic functionality. If additional features are needed, feel free to open an issue or submit a pull request.

### How It Works

- **Drag and Drop Inputs:**  
  Drag in the following assets into the tool:
  - **Idle**
  - **pose_l**
  - **pose_r**
  - **Skeleton** (placed at the top)

- **Animation Boxes:**  
  The bottom two boxes are designated for animations:
  - **Left Box:** For Additives, Gesture, or GesturePose animations.
  - **Right Box:** For Normal Animations.

## Mapping Editor

When adding to the mapping editor, the tool expects inputs in a specific format.

### Example Format

```text
Key                                 Values:
walk_offset_additive,walk_to_sprint sprint_in,1,1
```

### Breakdown

- **Keys:**  
  The first two keys represent the additive names in the file, for example:
  - `vm_p08_sn_ultiger_walk_offset_additive`
  - `vm_p08_sn_ultiger_walk_to_sprint`

- **Values:**  
  The next values specify the output file name and the type of animation.  
  In the example above, since the key `walk_to_sprint` is used, the output file is named:
  - `vm_p08_sn_ultiger_sprint_in`

- **Animation Type Codes:**  
  The numbers following the output file represent the type of animation:

  | Code | Animation Type         |
  | ---- | ---------------------- |
  | 0    | Normal Animation       |
  | 1    | Additive Animation     |
  | 2    | Gesture Animation      |
  | 3    | GesturePose Animation  |

  In the example, both `walk_offset_additive` and `walk_to_sprint` use the value `1`, which corresponds to **Additive Animation**.

## Contributing

If you have suggestions, encounter issues, or want to add new features, please feel free to raise an issue or contribute via pull requests.


