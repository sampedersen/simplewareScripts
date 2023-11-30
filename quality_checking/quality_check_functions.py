# Import operating system and Simpleware modules
import os
import scanip_api3 as sip

""" 
quality_check_functions.py 

This module contains the functions used during the segmentation quality checking process. 

Author: Sam Pedersen
Date: 2023-07-20
"""

"""
########################################################################################################################
                                                !!! README !!!
- This module is intended for use within Synopsys Simpleware ScanIP's scripting environment
- These functions *cannot* be executed outside Simpleware or within alternative IDEs
- Simpleware's scripting environment will not re-import modules within the same session; if any edits are made to this
    module, exit Simpleware entirely and begin a new session. Otherwise, Simpleware will continue executing the 
    originally imported version of the module
- Before using this module, it must be added to the path within Simpleware and imported. As a result, it is 
    recommended to run the other scripts hosted in the quality checking script folder, which are written with importing 
    settings and necessary functions called appropriately. 
#######################################################################################################################
"""


# Function to display message box
def message_box(msg):
    """

    Function to display a message within a pop-up dialogue box.

    :param msg: (str) Message to be displayed

    """
    # Display a dialogue box with a message
    sip.App.GetInstance().ShowMessage(msg)


# Verify that the module has been imported
def verify_import():
    """

    Verifies to the user that the module has been successfully imported to the Simpleware environment.

    """
    # Displays predetermined message within dialogue box
    message_box("Quality check module imported successfully!")


# Set masks to pre-established colors and order within Simpleware
def colors_order_visibility(color_palette):
    """

    Assigns tissues their respective colors and order of appearance within Simpleware.

    :param color_palette: (str) Indicate which palette, Sam's or Aprinda's, which will be implemented when setting
      tissue colors

    """

    # List of mask names
    masks = ["wm", "gm", "eyes", "csf", "air", "blood", "cancellous", "cortical", "skin", "fat", "muscle"]

    # Determine the color palette to use
    # If the user specifies for Aprinda's color palette, establish the color_dict with her values
    if color_palette == "Aprinda":
        color_dict = {
            "air": (0, 128, 0),
            "blood": (0, 0, 255),
            "cancellous": (255, 0, 255),
            "cortical": (0, 255, 0),
            "csf": (128, 0, 255),
            "eyes": (0, 128, 255),
            "fat": (246, 240, 202),
            "gm": (255, 128, 0),
            "muscle": (255, 64, 64),
            "skin": (0, 255, 255),
            "wm": (255, 128, 192),
        }

    # If the user specifies for Sam's color palette, establish the color_dict with her values
    elif color_palette == "Sam":
        color_dict = {
            "air": (65, 65, 65),
            "blood": (200, 0, 0),
            "cancellous": (22, 167, 11),
            "cortical": (0, 255, 0),
            "csf": (107, 220, 220),
            "eyes": (194, 230, 230),
            "fat": (239, 217, 151),
            "gm": (176, 176, 176),
            "muscle": (255, 64, 64),
            "skin": (140, 120, 83),
            "wm": (207, 221, 220),
        }

    # If the user specifies an unrecognized color palette, alert them and continue with Sam's palette
    else:
        msg = "Color palette designation not recognized. Please indicate \"Aprinda\" or \"Sam\". Continuing " \
              "with Sam\'s palette."
        message_box(msg)
        color_dict = {
            "air": (65, 65, 65),
            "blood": (200, 0, 0),
            "cancellous": (22, 167, 11),
            "cortical": (0, 255, 0),
            "csf": (107, 220, 220),
            "eyes": (194, 230, 230),
            "fat": (239, 217, 151),
            "gm": (176, 176, 176),
            "muscle": (255, 64, 64),
            "skin": (140, 120, 83),
            "wm": (207, 221, 220),
        }

    # Establish order of tissues
    order_dict = {
        "air": 7,
        "blood": 6,
        "cancellous": 5,
        "cortical": 4,
        "csf": 8,
        "eyes": 9,
        "fat": 2,
        "gm": 10,
        "muscle": 1,
        "skin": 3,
        "wm": 11
    }

    # For each mask...
    for mask in masks:
        # Establish variables
        name = mask
        color = color_dict[name]
        order = order_dict[name]

        # Select specific mask
        sip.App.GetDocument().GetGenericMaskByName(name).Activate()

        # Set color
        sip.App.GetDocument().GetActiveGenericMask().SetColour(sip.Colour(*color))

        # Set order
        sip.App.GetDocument().MoveMaskTo(sip.App.GetDocument().GetActiveGenericMask(), order)

        # Make visible
        sip.App.GetDocument().GetActiveGenericMask().SetVisible(True)


def import_mask(mask, location):
    """

    Function to import participant's mask from specified location.

    :param mask: (str) Mask intended to be imported
    :param location: (str) Path to participant's individual folder.


    """
    # Combine mask name and location info
    importInfo = f"{location}{mask}.raw"

    # Import tissue mask as background image
    sip.App.GetInstance().GetActiveDocument().ImportBackgroundFromRawImage(importInfo,
                                                                           sip.ImportOptions.UnsignedCharPixel, 256,
                                                                           256, 256, 1, 1, 1, 0,
                                                                           sip.ImportOptions.BinaryFile,
                                                                           sip.ImportOptions.LittleEndian,
                                                                           sip.CommonImportConstraints().SetWindowLevel(
                                                                               0, 0).SetCrop(0, 0, 0, 256, 256, 256)
                                                                           )
    # Rename background image to mask's name
    sip.App.GetDocument().GetBackgroundByName("Raw import [W:0.00 L:0.00]").SetName(f"{mask}_old")
    # Copy background image into mask
    sip.App.GetDocument().CopyBackgroundToMask()
    # Delete imported background image
    sip.App.GetDocument().RemoveBackground(sip.App.GetDocument().GetBackgroundByName(f"{mask}_old"))


def bone_patching():
    """

    Function to apply bone patching process to bone mask during QC.
    Requires "bone" be present in the sip file.

    """

    # Duplicate base bone masks to isolate large regions of skull
    sip.App.GetDocument().GetGenericMaskByName("bone").Activate()
    sip.App.GetDocument().GetActiveGenericMask().Duplicate()
    sip.App.GetDocument().GetGenericMaskByName("Copy of bone").SetName("unpatched_bone_regions")

    # Isolate regions thicker than 1 voxel and bigger than 15 voxels as an island
    sip.App.GetDocument().GetGenericMaskByName("unpatched_bone_regions").Activate()
    sip.App.GetDocument().ApplyErodeFilter(sip.Doc.TargetMask, 1, 1, 1, 0)
    sip.App.GetDocument().ApplyIslandRemovalFilter(15)

    # Redilate mask, intersect with original bone mask
    sip.App.GetDocument().ApplyDilateFilter(sip.Doc.TargetMask, 1, 1, 1, 0)
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression("(unpatched_bone_regions AND bone)",
                                                            sip.App.GetDocument().GetMaskByName(
                                                                "unpatched_bone_regions"),
                                                            sip.App.GetDocument().GetSliceIndices(
                                                                sip.Doc.OrientationXY),
                                                            sip.Doc.OrientationXY)

    # Duplicate to isolate small pieces, removing islands smaller than 15
    sip.App.GetDocument().GetGenericMaskByName("bone").Activate()
    sip.App.GetDocument().GetActiveGenericMask().Duplicate()
    sip.App.GetDocument().GetGenericMaskByName("Copy of bone").Activate()
    sip.App.GetDocument().GetGenericMaskByName("Copy of bone").SetName("patched_bone_regions_raw")
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression("(patched_bone_regions_raw MINUS unpatched_bone_regions)",
                                                            sip.App.GetDocument().GetMaskByName(
                                                                "patched_bone_regions_raw"),
                                                            sip.App.GetDocument().GetSliceIndices(
                                                                sip.Doc.OrientationXY),
                                                            sip.Doc.OrientationXY)
    sip.App.GetDocument().GetGenericMaskByName("patched_bone_regions_raw").Activate()
    sip.App.GetDocument().ApplyIslandRemovalFilter(15)
    # Duplicate and create patched mask
    sip.App.GetDocument().GetActiveGenericMask().Duplicate()
    sip.App.GetDocument().GetGenericMaskByName("Copy of patched_bone_regions_raw").Activate()
    sip.App.GetDocument().GetGenericMaskByName("Copy of patched_bone_regions_raw").SetName(
        "patched_bone_regions_corrected")
    sip.App.GetDocument().ApplyCloseFilter(sip.Doc.TargetMask, 2, 2, 2, 0)
    sip.App.GetDocument().ApplyDilateFilter(sip.Doc.TargetMask, 1, 1, 1, 0)
    # Remove potential overlap in interior region
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression("(patched_bone_regions_corrected MINUS wm)",
                                                            sip.App.GetDocument().GetMaskByName(
                                                                "patched_bone_regions_corrected"),
                                                            sip.App.GetDocument().GetSliceIndices(
                                                                sip.Doc.OrientationXY),
                                                            sip.Doc.OrientationXY)
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression("(patched_bone_regions_corrected MINUS gm)",
                                                            sip.App.GetDocument().GetMaskByName(
                                                                "patched_bone_regions_corrected"),
                                                            sip.App.GetDocument().GetSliceIndices(
                                                                sip.Doc.OrientationXY),
                                                            sip.Doc.OrientationXY)
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression("(patched_bone_regions_corrected MINUS csf)",
                                                            sip.App.GetDocument().GetMaskByName(
                                                                "patched_bone_regions_corrected"),
                                                            sip.App.GetDocument().GetSliceIndices(
                                                                sip.Doc.OrientationXY),
                                                            sip.Doc.OrientationXY)
    # Create patched bone mask
    sip.App.GetDocument().GetGenericMaskByName("patched_bone_regions_corrected").Activate()
    sip.App.GetDocument().GetActiveGenericMask().Duplicate()
    sip.App.GetDocument().GetGenericMaskByName("Copy of patched_bone_regions_corrected").Activate()
    sip.App.GetDocument().GetGenericMaskByName("Copy of patched_bone_regions_corrected").SetName("patched_bone")
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression("(patched_bone OR bone)",
                                                            sip.App.GetDocument().GetMaskByName("patched_bone"),
                                                            sip.App.GetDocument().GetSliceIndices(
                                                                sip.Doc.OrientationYZ),
                                                            sip.Doc.OrientationYZ)


# Remove the overlap between masks
def remove_overlap():
    """

    Removes the overlap/intersection between masks based on priority of tissues.

    """

    # Greymatter minus whitematter
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression("(gm MINUS wm)",
                                                            sip.App.GetDocument().GetMaskByName("gm"),
                                                            sip.App.GetDocument().GetSliceIndices(
                                                                sip.Doc.OrientationXY),
                                                            sip.Doc.OrientationXY)

    # Whitematter minus (eyes, csf)
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression("(wm MINUS eyes MINUS csf)",
                                                            sip.App.GetDocument().GetMaskByName("wm"),
                                                            sip.App.GetDocument().GetSliceIndices(
                                                                sip.Doc.OrientationXY),
                                                            sip.Doc.OrientationXY)

    # Air minus (wm, gm, csf, blood, skin)
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression("(air MINUS wm MINUS gm MINUS csf MINUS blood MINUS skin)",
                                                            sip.App.GetDocument().GetMaskByName("air"),
                                                            sip.App.GetDocument().GetSliceIndices(
                                                                sip.Doc.OrientationXY),
                                                            sip.Doc.OrientationXY)

    # Blood minus (wm, gm, eyes, skin)
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression("(blood MINUS wm MINUS gm MINUS eyes MINUS skin)",
                                                            sip.App.GetDocument().GetMaskByName("blood"),
                                                            sip.App.GetDocument().GetSliceIndices(
                                                                sip.Doc.OrientationXY),
                                                            sip.Doc.OrientationXY)

    # Cortical minus (wm, gm, air, eyes, blood)
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression(
        "(cortical MINUS wm MINUS gm MINUS air MINUS eyes MINUS blood)",
        sip.App.GetDocument().GetMaskByName("cortical"),
        sip.App.GetDocument().GetSliceIndices(sip.Doc.OrientationXY),
        sip.Doc.OrientationXY)

    # Cancellous minus (wm, gm, air, eyes, blood)
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression(
        "(cancellous MINUS wm MINUS gm MINUS air MINUS eyes MINUS blood)",
        sip.App.GetDocument().GetMaskByName("cancellous"),
        sip.App.GetDocument().GetSliceIndices(sip.Doc.OrientationXY),
        sip.Doc.OrientationXY)

    # Cortical minus (skin, cancellous, csf)
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression("(cortical MINUS skin MINUS cancellous MINUS csf)",
                                                            sip.App.GetDocument().GetMaskByName("cortical"),
                                                            sip.App.GetDocument().GetSliceIndices(
                                                                sip.Doc.OrientationXY),
                                                            sip.Doc.OrientationXY)

    # Cancellous minus (skin, csf)
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression("(cancellous MINUS skin MINUS csf)",
                                                            sip.App.GetDocument().GetMaskByName("cancellous"),
                                                            sip.App.GetDocument().GetSliceIndices(
                                                                sip.Doc.OrientationXY),
                                                            sip.Doc.OrientationXY)

    # Fat minus (skin, wm, gm, eyes, air, blood, cortical, cancellous, csf)
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression(
        "(fat MINUS skin MINUS wm MINUS gm MINUS eyes MINUS air MINUS blood MINUS cortical MINUS cancellous MINUS csf)",
        sip.App.GetDocument().GetMaskByName("fat"), sip.App.GetDocument().GetSliceIndices(sip.Doc.OrientationXY),
        sip.Doc.OrientationXY)

    # Muscle minus (skin, wm, gm, eyes, air, blood, cortical, cancellous, csf, fat)
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression(
        "(muscle MINUS skin MINUS wm MINUS gm MINUS eyes MINUS air MINUS blood MINUS cortical MINUS cancellous MINUS csf MINUS fat)",
        sip.App.GetDocument().GetMaskByName("muscle"), sip.App.GetDocument().GetSliceIndices(sip.Doc.OrientationXY),
        sip.Doc.OrientationXY)

    # Eyes minus skin
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression("(eyes MINUS skin)",
                                                            sip.App.GetDocument().GetMaskByName("eyes"),
                                                            sip.App.GetDocument().GetSliceIndices(
                                                                sip.Doc.OrientationXY),
                                                            sip.Doc.OrientationXY)

    # CSF minus eyes
    sip.App.GetDocument().ReplaceMaskUsingBooleanExpression("(csf MINUS eyes)",
                                                            sip.App.GetDocument().GetMaskByName("csf"),
                                                            sip.App.GetDocument().GetSliceIndices(
                                                                sip.Doc.OrientationXY),
                                                            sip.Doc.OrientationXY)


# Generate the initial quality check #1 .sip file
def generate_base_file(participant_id, folder_location):
    """

    Creates a new .sip file by loading in the participant's T1.RAW, imports tissue masks, sets the masks' colors and
    orders, pre-processes bone (if available), and saves within the participant's quality checking folder

    :param participant_id: (int) Participant's 6-digit identifying number (ie, 999999 or 103485)
    :param folder_location: (str) Directory location that the participant's individual folder is contained within

    """

    # Establish participant's folder and location
    participant_folder = f"{folder_location}FS6.0_sub-{str(participant_id)}_ses01\\"

    # Check for T1.raw:
    # Participant's T1s usually exist within their base participant folder, but may exist in
    # potentially one of two formats:
    #   - FS6.0_sub-999999_ses01_T1_rs.RAW
    #   - T1.RAW
    # The following for loop will check if either of these versions exist in the participant's folder;
    # if one version exists, it will continue the following functions; if it is unable to find either version in the
    # participant's folder, it not generate the file and will display a message indicate such.

    # Checking for T1.raw:
    # Preallocate T1 variable
    t1 = None
    # Naming structure, option 1
    t1_name1 = f"FS6.0_sub-{str(participant_id)}_ses01_T1_rs.RAW"
    # Naming structure, option 2
    t1_name2 = "T1.RAW"
    # List of T1 naming options (1 and 2)
    t1_names = [t1_name1, t1_name2]

    # Check the T1 naming structure
    # For each naming option...
    for name in t1_names:
        # Identify t1_path as the full pathway to the participant's folder combined with each naming version
        t1_path = participant_folder + name
        # If a version of the T1 exists in the participant's folder...
        if os.path.exists(t1_path):
            t1 = t1_path  # ... set T1 to be the T1 path location and...
            break  # ... stop looking for a T1.

    # If the T1 was not locatable, display a dialogue box indicating such
    if not t1:
        message_box("No RAW T1 scan found.")

    # If able to locate a T1 file:
    else:
        # Load the T1 into a new sip file
        # Rename background image as <participant_id>_T1
        sip.App.GetInstance().ImportRawImage(t1,
                                             sip.ImportOptions.DoublePixel, 256, 256, 256, 1.0, 1.0, 1.0, 0,
                                             sip.ImportOptions.BinaryFile, sip.ImportOptions.LittleEndian,
                                             sip.CommonImportConstraints().SetWindowLevel(0.0, 0.0).SetCrop(0, 0, 0,256, 256,256).SetPixelType(sip.Doc.Float32)
                                             )
        sip.App.GetDocument().GetBackgroundByName("Raw import [W:0.00 L:0.00]").SetName(str(participant_id) + "_T1")

        # IMPORTING PROCEDURES -----------------------------------------------------------------------------------------

        # Begin importing final tissue masks
        # Establish location for finalized masks from participant's folder
        mask_location = participant_folder + "Binarized_masks\\idv_mask\\"
        # List of masks to be imported
        masks = ["wm", "gm", "eyes", "csf", "air", "blood", "cancellous", "cortical", "skin", "fat", "muscle"]

        # For each mask in the list...
        for mask in masks:
            # ... Set the name as the particular mask...
            mask_name = mask
            # ... Import info, combining the mask name and import source location...
            import_info = mask_location + mask_name + ".raw"

            # ... Import tissue mask as background image...
            sip.App.GetInstance().GetActiveDocument().ImportBackgroundFromRawImage(
                import_info,
                sip.ImportOptions.UnsignedCharPixel, 256, 256, 256, 1, 1, 1, 0,
                sip.ImportOptions.BinaryFile, sip.ImportOptions.LittleEndian,
                sip.CommonImportConstraints().SetWindowLevel(0, 0).SetCrop(0, 0, 0, 256, 256, 256)
            )
            # ... Rename background image to mask's name...
            sip.App.GetDocument().GetBackgroundByName("Raw import [W:0.00 L:0.00]").SetName(mask_name)
            # ... Copy background image into mask...
            sip.App.GetDocument().CopyBackgroundToMask()
            # ... Delete imported background image
            sip.App.GetDocument().RemoveBackground(sip.App.GetDocument().GetBackgroundByName(mask_name))

        # Colors and order
        colors_order_visibility("Sam")

        # Check if uniform is available
        if os.path.exists(f"{participant_folder}Binarized_masks\\final\\uniform.raw"):
            # Indicator
            import_uniform = True
            # Est path as such
            uniform_file = f"{participant_folder}Binarized_masks\\final\\"
        # Else, if uniform exists within the bin_masks folder...
        elif os.path.exists(f"{participant_folder}Binarized_masks\\uniform.raw"):
            # Indicator:
            import_uniform = True
            # Est path as such
            uniform_file = f"{participant_folder}Binarized_masks\\"
        # Else, set the uniform_file path to "NONE", notify user later
        else:
            import_uniform = False
            uniform_file = "NONE"
        # If a uniform mask is available, import it
        if import_uniform:
            import_mask("uniform", uniform_file)
            sip.App.GetDocument().GetGenericMaskByName("uniform_old").SetName("uniform")

        # BONE PRE-PROCESSING PROCEDURES   -----------------------------------------------------------------------------

        # Check for available bone:
        # If the bone exists within the bin_masks\final folder...
        if os.path.exists(f"{participant_folder}Binarized_masks\\final\\bone.raw"):
            # Indicator
            import_bone = True
            # Est path as such
            bone_file = f"{participant_folder}Binarized_masks\\final\\"
        # Else, if bone exists within the bin_masks folder...
        elif os.path.exists(f"{participant_folder}Binarized_masks\\bone.raw"):
            # Indicator:
            import_bone = True
            # Est path as such
            bone_file = f"{participant_folder}Binarized_masks\\"
        # Else, set the bone_file path to "NONE", notify user later
        else:
            import_bone = False
            bone_file = "NONE"

        # If a bone mask is available import it and perform bone patching
        if import_bone:
            # Import the bone
            import_mask("bone", bone_file)
            sip.App.GetDocument().GetGenericMaskByName("bone_old").SetName("bone")

            # Perform bone patching
            bone_patching()

            # If uniform was imported, reorganize masks with consideration to that
            if import_uniform:
                # Organize additional bone + uniform masks
                # Create a divider mask
                sip.App.GetDocument().CreateMask("---", sip.Colour(0, 255, 63))

                # Move patched_bone_regions_corrected
                sip.App.GetDocument().GetGenericMaskByName("patched_bone_regions_corrected").Activate()
                sip.App.GetDocument().MoveMaskTo(sip.App.GetDocument().GetActiveGenericMask(), 17)

                # Move patched_bone_regions_raw
                sip.App.GetDocument().GetGenericMaskByName("patched_bone_regions_raw").Activate()
                sip.App.GetDocument().MoveMaskTo(sip.App.GetDocument().GetActiveGenericMask(), 16)

                # Move unpatched_bone_regions
                sip.App.GetDocument().GetGenericMaskByName("unpatched_bone_regions").Activate()
                sip.App.GetDocument().MoveMaskTo(sip.App.GetDocument().GetActiveGenericMask(), 15)

                # Create a divider mask
                sip.App.GetDocument().CreateMask("----", sip.Colour(0, 159, 255))

                # Move patched_bone
                sip.App.GetDocument().GetGenericMaskByName("patched_bone").Activate()
                sip.App.GetDocument().MoveMaskTo(sip.App.GetDocument().GetActiveGenericMask(), 18)

                # Move bone
                sip.App.GetDocument().GetGenericMaskByName("bone").Activate()
                sip.App.GetDocument().MoveMaskTo(sip.App.GetDocument().GetActiveGenericMask(), 17)

                # Move uniform
                sip.App.GetDocument().GetGenericMaskByName("uniform").Activate()
                sip.App.GetDocument().MoveMaskTo(sip.App.GetDocument().GetActiveGenericMask(), 16)

                # Move dividers
                sip.App.GetDocument().GetGenericMaskByName("---").Activate()
                sip.App.GetDocument().MoveMaskTo(sip.App.GetDocument().GetActiveGenericMask(), 12)
                sip.App.GetDocument().GetGenericMaskByName("----").Activate()
                sip.App.GetDocument().MoveMaskTo(sip.App.GetDocument().GetActiveGenericMask(), 16)

        # FINALIZING ---------------------------------------------------------------------------------------------------

        # Save file as <999999>_base.sip to participant's quality checking folder
        qc_save = f"{participant_folder}qualityCheck\\sipFiles\\{str(participant_id)}_base.sip"
        sip.App.GetDocument().SaveAs(qc_save)

        # If the uniform mask and/or bone mask DNE, notify user:
        # If uniform AND bone both DNE:
        if not import_uniform and not import_bone:
            message = "Could not find files for either uniform or bone masks."
        elif not import_uniform and import_bone:
            message = "Bone imported but uniform could not be located."
        elif not import_bone and import_uniform:
            message = "Uniform imported but bone could not be located."
        else:
            message = f"{participant_id}_base.sip successfully generated. Uniform and pre-patched bone included."
        message_box(message)

# Finalize the .sip file, save and export tissues
def finalize_sip_file(participant_id, folder_location, check_stage):
    """

    Standardizes the colors/order/visibility of the masks in the .sip file before removing intersecting overlap,
    binarizing and exporting the tissue masks to the quality check folder, and saving the .sip file.

    :param participant_id: (int) Participant's 6-digit identifying number (ie, 999999 or 103485)
    :param folder_location: (str) Directory location that the participant's individual folder is contained within
    :param check_stage: (int) Should be either 1 or 2 to indicate if this is the end of quality check #1 or #2

    """

    # Establish participant's folder and export location
    participantFolder = f"{folder_location}FS6.0_sub-{participant_id}_ses01\\qualityCheck\\"
    exportLocation = f"{participantFolder}tissueMasks\\"

    # If tissueMasks directory DNE, make it
    if not os.path.exists(exportLocation):
        os.makedirs(exportLocation)

    # Masks to binarize/export
    masks = ["wm", "gm", "eyes", "csf", "air", "blood", "cancellous", "cortical", "skin", "fat", "muscle"]

    # Standardize colors and order
    colors_order_visibility("Aprinda")
    # Separate masks
    remove_overlap()

    # Binarize and export tissue masks
    for mask in masks:
        name = mask
        exportingMask = exportLocation + name + ".raw"

        # Binarize
        sip.App.GetDocument().GetGenericMaskByName(name).Activate()
        sip.App.GetDocument().ApplyBinarisationFilter()

        # Export the mask
        sip.App.GetDocument().GetMaskByName(name).RawExport(exportingMask)

    # Save project
    sip.App.GetDocument().SaveAs(f"{participantFolder}sipFiles\\{participant_id}_QC{check_stage}.sip")


# Function to close out current participant and generate next quality check file
def stop_start_visual_checks(current_participant, next_participant, folder_location):
    """

    Function to streamline the visual checking process by closing and saving the current file before generating and
    opening the next participant's base file.

    :param current_participant: (int) Current participant's 6-digit identifier (ex, 999999)
    :param next_participant: (int)  Next participant's 6-digit identifier (ex, 888888)
    :param folder_location: (str) Directory location that the participant's individual folder is contained within

    """

    # Save current file as <current_participant>_base.sip
    participantFolder = f"{folder_location}FS6.0_sub-{current_participant}_ses01\\qualityCheck\\"
    sip.App.GetDocument().SaveAs(f"{participantFolder}sipFiles\\{current_participant}_base.sip")

    # Close out current file
    sip.App.GetDocument().Close()
    # Generate next participant file
    generate_base_file(next_participant, folder_location)


