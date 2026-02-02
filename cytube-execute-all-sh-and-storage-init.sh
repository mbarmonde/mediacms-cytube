#!/bin/bash

# dev-v0.1.5

#####
# v0.1.5 - Integrated all files into GitHub pull - Only for chmod all files to execute and storage config
# v0.1.4 - Final script for alt root folder copy 
#- Added a way to copy certificates to caddy/caddy/certificates for dev.420grindhouseserver.com helping not hit the limit for minting a new cert, hitting the ACME limits
#- Changed location for coredev3
#- added automatic chmod +x for all .sh files
#- added validation script execution after copy
#- added scripts folder for the healthcheck for nginx commenting
#- removed media_files/custom and moved the cytube-export.js to static/js
#- added a new location for the nginx configuration to add to docker compose
#- Changed location for coredev2
#- Initial release
#####

# chmod +x (filename).sh to make executable
#./(filename) to run in CLI
## modified for dev at the CORE_DIR

## Define the core directory in root
# CORE_DIR="/coredev4"

# Define destination directory
DEST_DIR="/mediacms"

## Include both top-level and nested folders
# TARGET_FOLDERS=(
    "caddy"
    "caddy/caddy/certificates"
    "cms"
    "deploy/docker"
    "deploy/docker/nginx"
    "scripts"
    "static/js"
    "templates"
)

## Create destination directory if it doesn't exist
# mkdir -p "$DEST_DIR"

## First, copy files from the root of CORE_DIR
#echo "Copying files from root of $CORE_DIR"
#if [ -d "$CORE_DIR" ]; then
    ## Copy only files (not directories) from the root
    # find "$CORE_DIR" -maxdepth 1 -type f -exec cp -v {} "$DEST_DIR/" \;
#fi

## Then loop through each target subfolder
#for folder in "${TARGET_FOLDERS[@]}"
#do
    #SOURCE="${CORE_DIR}/${folder}"

    #if [ -d "$SOURCE" ]; then
        #echo "Copying files from $SOURCE"

        ## Create nested destination structure
        #mkdir -p "$DEST_DIR/$folder"

        ## Copy all files from the folder
        #cp -rv "$SOURCE"/* "$DEST_DIR/$folder/"
    #else
        #echo "Warning: $SOURCE does not exist, skipping..."
    #fi
#done

#echo "Copy operation completed"

## Make all .sh files executable
echo "Making all .sh files executable..."
find "$DEST_DIR" -type f -name "*.sh" -exec chmod +x {} \;
echo "All .sh files are now executable"

## Run validation script if it exists
VALIDATION_SCRIPT="$DEST_DIR/scripts/init_validate_storage.sh"
if [ -f "$VALIDATION_SCRIPT" ]; then
    echo "Running validation script..."
    "$VALIDATION_SCRIPT"
else
    echo "Warning: Validation script not found at $VALIDATION_SCRIPT"
fi
