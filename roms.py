#!/usr/bin/env python3

import argparse
import copy
import hashlib
import logging
import os
import pathlib
import re
import shutil
import sys


def copy_whitelisted_files(console, dest_dir, base_dir):
    console_dest_dir = dest_dir + "/" + console
    whitelist_file = base_dir + "/" + console + "/whitelist.auto.txt"

    # Prompt to create console dir
    if not os.path.isdir(console_dest_dir):
        create_dir(console, console_dest_dir)

    with open(whitelist_file) as f:
        whitelist = f.read().splitlines()

    # Copy whitelisted destination files
    if len(whitelist) >= 1:
        logging.info(console + ": updating whitelisted files to " +
                     console_dest_dir + "...")

        def get_hash(file):
            file_hash = hashlib.blake2b(pathlib.Path(
                file).read_bytes()).hexdigest()

            return file_hash

        for f in whitelist:
            dest_file = os.path.join(console_dest_dir + "/" + f.rstrip())
            src_file = os.path.join(
                base_dir + "/" + console + "/" + f.rstrip())

            dest_hash = ""
            src_hash = get_hash(src_file)
            if os.path.isfile(dest_file):
                dest_hash = get_hash(dest_file)

            if not os.path.isfile(dest_file) or dest_hash != src_hash:
                shutil.copy2(src_file, dest_file)

                dest_hash = get_hash(dest_file)

                if dest_hash == src_hash:
                    logging.info(console + ": copied " +
                                 os.path.basename(f.rstrip()))
                else:
                    logging.critical(console + ": hash sum mismatch (I/O error?), exiting!: " +
                                     f.rstrip())
            elif dest_hash == src_hash:
                logging.info(console + ": verified " +
                             os.path.basename(f.rstrip()))

    logging.info(console + ": whitelisted destination files are up-to-date")


def create_dir(console, path):

    def mkdir(path):
        os.mkdir(path)

        if not os.path.isdir(path):
            logging.critical(console + ": failed to create directory, exiting!: " +
                             path)
            exit(1)
        else:
            logging.info(console + ": created: " + path)

    if not args.initialize:
        logging.warning(console + ": " + path +
                        " does NOT exist, create it? y/N:")
        create = input()
        if create == "y" or create == "Y":
            mkdir(path)
        else:
            logging.critical(console + ": unable to proceed, exiting!")
            exit(1)
    else:
        mkdir(path)


def delete_blacklisted_files(console, dest_dir, base_dir):
    blacklist_file = base_dir + "/" + console + "/blacklist.auto.txt"
    console_dest_dir = dest_dir + "/" + console

    # Confirm final destinaton exists
    if not os.path.isdir(console_dest_dir):
        logging.critical(console + ": path does NOT exist, exiting!: " +
                         console_dest_dir)
        exit(1)

    # Get list of destination files
    dest_files = [f for f in os.listdir(
        console_dest_dir) if os.path.isfile(os.path.join(console_dest_dir, f))]

    with open(blacklist_file) as f:
        blacklist = f.read().splitlines()

    # Delete blacklisted destination files
    delete_files = [item for item in blacklist if item in dest_files]
    for f in delete_files:
        file_name = os.path.join(console_dest_dir, f.rstrip())
        try:
            os.remove(file_name)
            logging.info(console + ": deleted " +
                         f.rstrip())
        except OSError as e:
            if e.errno != errno.ENOENT:  # Ignore "No such file or directory"
                raise

    logging.info(console + ": blacklisted destination files are up-to-date")


def generate_lists(console, base_dir):
    console_path = base_dir + "/" + console

    # Prompt to create console dir
    if not os.path.isdir(console_path):
        create_dir(console, console_path)

    # Initial list of files in console dir
    filelist = [f for f in os.listdir(
        console_path) if os.path.isfile(os.path.join(console_path, f))]

    # Remove ignored files by extension
    ignored_extensions_regex = "(?!.*\.txt$)(?!.*\.auto$)(?!.*\.png$)(?!.*\.srm$)(?!.*\.xml$)"
    filelist = list(
        filter(lambda v: re.match(ignored_extensions_regex, v), filelist))

    # Replace "Enhance" with "TEMPORARY" to guarantee "(En)" search result accuracy
    filelist = [file.replace('Enhance', 'TEMPORARY') for file in filelist]

    # Blacklist [b], (Beta), [BIOS], (Demo), (Pirate), (Program), (Proto), and (Sample)
    regex_bios = ".*\[b\].*|.*\(.*Beta.*\).*|.*[Bb][Ii][Oo][Ss].*|.*\(.*Demo.*\).*|.*\(.*Pirate.*\).*|.*\(.*Program.*\).*|.*\(.*Proto.*\).*|.*\(.*Sample.*\).*"
    blacklist = list(
        filter(lambda v: re.match(regex_bios, v), filelist))

    # Blacklist files that are not (U), (USA), (World), (En)
    regex_not_english = "(?!.*\(U\).*)(?!.*\(.*USA.*\).*)(?!.*\(.*World.*\).*)(?!.*\(.*En.*\).*)"
    blacklist = blacklist + list(
        filter(lambda v: re.match(regex_not_english, v), filelist))

    # Replace "TEMPORARY" with "Enhance"
    blacklist = [file.replace('TEMPORARY', 'Enhance') for file in blacklist]

    # Add blacklist custom (if it exists) to blacklist auto
    blacklist_custom_path = console_path + "/blacklist.custom.txt"
    if os.path.exists(blacklist_custom_path):
        with open(blacklist_custom_path) as blacklist_custom:
            blacklist = blacklist + blacklist_custom.read().splitlines()

    # Whitelist files that are (U), (USA), (World), (En)
    regex_english = ".*\(U\).*|.*\(.*USA.*\).*|.*\(.*World.*\).*|.*\(.*En.*\).*"

    whitelist = list(
        filter(lambda v: re.match(regex_english, v), filelist))

    # Whitelist files that are not [b], (Beta), [BIOS], (Demo), (Pirate), (Program), (Proto), or (Sample)
    regex_not_bios = [
        "(?!.*\[b\].*)", "(?!.*\(.*Beta.*\).*)", "(?!.*[Bb][Ii][Oo][Ss].*)", "(?!.*\(.*Demo.*\).*)", "(?!.*\(.*Pirate.*\).*)", "(?!.*\(.*Program.*\).*)", "(?!.*\(.*Proto.*\).*)", "(?!.*\(.*Sample.*\).*)"]

    for regex in regex_not_bios:
        whitelist = list(
            filter(lambda v: re.match(regex, v), whitelist))

    # Replace "TEMPORARY" with "Enhance"
    whitelist = [file.replace('TEMPORARY', 'Enhance') for file in whitelist]

    # List filenames including Rev
    regex_revision = ".*\(Rev.*\d\).*"

    rev_files = list(
        filter(lambda v: re.match(regex_revision, v), whitelist))

    # Build dictionaries containing filenames and Revs
    rev_dict_all = {}

    for f in rev_files:
        filename_without_rev = re.sub(
            "\(Rev.*\d\)", "REPLACE_WITH_REV", f)

        rev = re.findall("\(Rev.*\d\)", f)[0]

        if filename_without_rev not in rev_dict_all:
            rev_dict_all.update({filename_without_rev: {
                "revisions": [rev]
            }})
        else:
            rev_dict_all[filename_without_rev]["revisions"].append(
                rev)

    # Copy the dict because it's unsafe to modify the original data structure while iterating over it
    rev_dict_min = copy.deepcopy(rev_dict_all)

    # Whitelist greatest Revs
    for filename in rev_dict_all:
        # Get the greatest Rev and whitelist it
        max_ver = max(rev_dict_all[filename]["revisions"])

        game_file = re.sub(
            "REPLACE_WITH_REV", max_ver, filename)

        whitelist = whitelist + [game_file]

        # Remove the greatest Rev from the minor Rev dictionary
        rev_dict_min[filename]["revisions"].remove(
            max(rev_dict_all[filename]["revisions"]))

        # Get the filename without any Rev
        game_file = re.sub(
            " REPLACE_WITH_REV", "", filename)

        # Confirm the reconstructed filename exists
        if os.path.exists(console_path + "/" + game_file):
            # Keep the whitelist in sync
            try:
                whitelist.remove(game_file)
            except:
                pass

            # Blacklist the filename without any Rev
            blacklist = blacklist + [game_file]

    # Blacklist all inferior Revs
    for filename in rev_dict_min:
        for rev in rev_dict_min[filename]["revisions"]:
            game_file = re.sub(
                "REPLACE_WITH_REV", rev, filename)

        # Confirm the reconstructed filename exists
        if os.path.exists(console_path + "/" + game_file):
            # Keep the whitelist in sync
            try:
                whitelist.remove(game_file)
            except:
                pass

            blacklist = blacklist + [game_file]

    # Alphabetize and remove duplicates
    blacklist = sorted(
        list(dict.fromkeys(blacklist)))

    # Subtract blacklist auto from whitelist auto
    whitelist = [item for item in whitelist if item not in blacklist]

    # Add whitelist custom (if it exists) to whitelist auto
    whitelist_custom_path = console_path + "/whitelist.custom.txt"
    if os.path.exists(whitelist_custom_path):
        with open(whitelist_custom_path) as whitelist_custom:
            whitelist = whitelist + whitelist_custom.read().splitlines()

    # Alphabetize and remove duplicates
    whitelist = sorted(
        list(dict.fromkeys(whitelist)))

    # Subtract whitelist auto from blacklist auto, finalize blacklist auto
    blacklist = [item for item in blacklist if item not in whitelist]

    # Write whitelist to file
    whitelist_path = console_path + "/whitelist.auto.txt"
    with open(whitelist_path, "w") as white_file:
        for file_line in whitelist:
            white_file.write('%s\n' % file_line)
    logging.info(console + ": blacklist generated")

    # Write blacklist to file
    blacklist_path = console_path + "/blacklist.auto.txt"
    with open(blacklist_path, "w") as black_file:
        for file_line in blacklist:
            black_file.write('%s\n' % file_line)
    logging.info(console + ": whitelist generated")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
        level=logging.INFO,
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler()],
    )

    description = "Automatically filter video game roms using blacklists and whitelists and (optionally) transfer them."

    parser = argparse.ArgumentParser(
        description=description)
    parser.add_argument("--base-dir")
    parser.add_argument("--console-name", required=True)
    parser.add_argument("--destination-dir")
    parser.add_argument("--initialize", action='store_true')
    args = parser.parse_args()

    if not args.base_dir:
        logging.warning(
            "missing --base-dir argument, falling back to current working directory (" + os.getcwd() + ")!")
        base_dir = os.getcwd()
    else:
        base_dir = args.base_dir

    if args.console_name == "all":
        console_dirs = ["gb", "gba", "gbc", "genesis",
                        "n64", "nes", "psp", "psx", "snes"]
    else:
        console_dirs = [args.console_name]

    if not args.destination_dir:
        logging.warning(
            "missing --destination-dir argument, NOT syncing files to destination directory!")

    for console in console_dirs:
        generate_lists(console, base_dir)

        if args.destination_dir:
            copy_whitelisted_files(console, args.destination_dir, base_dir)
            delete_blacklisted_files(console, args.destination_dir, base_dir)
