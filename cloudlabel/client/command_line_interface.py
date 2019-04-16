#!/usr/bin/env python
# encoding: utf-8
"""
command.py

Created by Pierre-Julien Grizel et al.
Copyright (c) 2016 NumeriCube. All rights reserved.

A command-line script to upload/download datasets to CLOUDLABEL
"""
from __future__ import unicode_literals

__author__ = ""
__copyright__ = "Copyright 2016, NumeriCube"
__credits__ = ["Pierre-Julien Grizel"]
__license__ = "CLOSED SOURCE"
__version__ = "TBD"
__maintainer__ = "Pierre-Julien Grizel"
__email__ = "pjgrizel@numericube.com"
__status__ = "Production"

import pprint
import argparse
import urllib
import json
import os

import tqdm
import slumber
import requests

import cloudlabel.client


def get_client_from_args(parsed_args):
    """Get cloudlabel client
    """
    return cloudlabel.client.Client(
        project_slug=parsed_args.project,
        username=parsed_args.username,
        token=parsed_args.token,
        api_url=parsed_args.api_url,
    )


def upload_dir(parsed_args):
    """Upload a whole directory to your cloudlabel.client instance.
    """
    client = get_client_from_args(parsed_args)
    kwargs = dict(path=parsed_args.path, create_tags=parsed_args.create_tags)
    if parsed_args.dry_run:
        response = client.dataset().test_zip(**kwargs)
    else:
        response = client.dataset().upload_dir(**kwargs)
    pprint.pprint(response)


def sync(parsed_args):
    """Synchronize your local cache directory with the remote project.
    """
    # Fetch target assets
    api = slumber.API(parsed_args.api_url)
    assets = api.projects(parsed_args.project).assets.get()

    # Download thumbnails
    for asset in tqdm.tqdm(assets):
        # Download file locally
        if asset['thumbnail_320x200']:
            filename = os.path.split(urllib.parse.urlparse(asset['thumbnail_320x200']).path)[-1]
            if not os.path.isfile(filename):
                response = requests.get(asset['thumbnail_320x200'])
                with open(filename, 'wb') as thumbnail_file:
                    thumbnail_file.write(response.content)

            # Append reference to the local path
            asset["thumbnail_320x200_path"] = filename

    # Save the resulting JSON file
    with open("{}-assets.json".format(parsed_args.project), "w") as json_file:
        json.dump(assets, json_file, indent=4, sort_keys=True)


def main():
    """main entry point
    """
    # Main parser and CMD line features
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="Project slug to connect to")
    parser.add_argument(
        "--username",
        default=os.environ.get("CLOUDLABEL_USERNAME"),
        help="Your CloudLabel username",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("CLOUDLABEL_TOKEN"),
        help="Your CloudLabel secret token",
    )
    parser.add_argument(
        "--api-url", help="API URL", default="http://localhost:8000/api/v1/", required=True,
    )
    subparsers = parser.add_subparsers(
        help="execute this command",
        title="subcommands",
        description="valid subcommands",
        dest="subcommand",
    )
    subparsers.required = (
        True
    )  # New in Py3, see https://stackoverflow.com/questions/22990977/why-does-this-argparse-code-behave-differently-between-python-2-and-3

    # Parser for the simple "sync" command
    parser_sync = subparsers.add_parser("sync", help=sync.__doc__)
    # parser_sync.add_argument("api_url", help="Full API URL of your project")
    # parser_sync.add_argument("project_name", help="The project name you want to sync", default=None)
    parser_sync.set_defaults(func=sync)

    # create the parser for the "upload_dir" command
    parser_upload_dir = subparsers.add_parser("upload_dir", help=upload_dir.__doc__)
    parser_upload_dir.add_argument("path", help="directory to upload")
    parser_upload_dir.add_argument(
        "--create-tags",
        action="store_true",
        help="Create tags on-the-fly",
        default=False,
    )
    parser_upload_dir.add_argument(
        "--dry-run", action="store_true", help="Don't do it for real", default=False
    )
    parser_upload_dir.set_defaults(func=upload_dir)

    # create the parser for the "individual upload" command
    parser_upload = subparsers.add_parser("upload", help=upload_dir.__doc__)
    parser_upload.add_argument("path", help="file to upload")
    parser_upload.set_defaults(func=upload_dir)

    # Let's conclude this
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
