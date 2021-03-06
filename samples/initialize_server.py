####
# This script sets up a server. It uploads datasources and workbooks from the local filesystem.
#
# By default, all content is published to the Default project on the Default site.
####

import tableauserverclient as TSC
import argparse
import getpass
import logging
import glob


def main():
    parser = argparse.ArgumentParser(description='Initialize a server with content.')
    parser.add_argument('--server', '-s', required=True, help='server address')
    parser.add_argument('--datasources-folder', '-df', required=True, help='folder containing datasources')
    parser.add_argument('--workbooks-folder', '-wf', required=True, help='folder containing workbooks')
    parser.add_argument('--site', '-si', required=False, default='Default', help='site to use')
    parser.add_argument('--project', '-p', required=False, default='Default', help='project to use')
    parser.add_argument('--username', '-u', required=True, help='username to sign into server')
    parser.add_argument('--logging-level', '-l', choices=['debug', 'info', 'error'], default='error',
                        help='desired logging level (set to error by default)')
    args = parser.parse_args()

    password = getpass.getpass("Password: ")

    # Set logging level based on user input, or error by default
    logging_level = getattr(logging, args.logging_level.upper())
    logging.basicConfig(level=logging_level)

    ################################################################################
    # Step 1: Sign in to server.
    ################################################################################
    tableau_auth = TSC.TableauAuth(args.username, password)
    server = TSC.Server(args.server)

    with server.auth.sign_in(tableau_auth):

        ################################################################################
        # Step 2: Create the site we need only if it doesn't exist
        ################################################################################
        print("Checking to see if we need to create the site...")

        all_sites, _ = server.sites.get()
        existing_site = next((s for s in all_sites if s.name == args.site), None)

        # Create the site if it doesn't exist
        if existing_site is None:
            print("Site not found: {0} Creating it...").format(args.site)
            new_site = TSC.SiteItem(name=args.site, content_url=args.site.replace(" ", ""),
                                    admin_mode=TSC.SiteItem.AdminMode.ContentAndUsers)
            server.sites.create(new_site)
        else:
            print("Site {0} exists. Moving on...").format(args.site)

    ################################################################################
    # Step 3: Sign-in to our target site
    ################################################################################
    print("Starting our content upload...")
    server_upload = TSC.Server(args.server)
    tableau_auth.site = args.site

    with server_upload.auth.sign_in(tableau_auth):

        ################################################################################
        # Step 4: Create the project we need only if it doesn't exist
        ################################################################################
        all_projects, _ = server_upload.projects.get()
        project = next((p for p in all_projects if p.name == args.project), None)

        # Create our project if it doesn't exist
        if project is None:
            print("Project not found: {0} Creating it...").format(args.project)
            new_project = TSC.ProjectItem(name=args.project)
            project = server_upload.projects.create(new_project)

        ################################################################################
        # Step 5:  Set up our content
        #     Publish datasources to our site and project
        #     Publish workbooks to our site and project
        ################################################################################
        publish_datasources_to_site(server_upload, project, args.datasources_folder)
        publish_workbooks_to_site(server_upload, project, args.workbooks_folder)


def publish_datasources_to_site(server_object, project, folder):
    path = folder + '/*.tds*'

    for fname in glob.glob(path):
        new_ds = TSC.DatasourceItem(project.id)
        new_ds = server_object.datasources.publish(new_ds, fname, server_object.PublishMode.Overwrite)
        print("Datasource published. ID: {0}".format(new_ds.id))


def publish_workbooks_to_site(server_object, project, folder):
    path = folder + '/*.twb*'

    for fname in glob.glob(path):
        new_workbook = TSC.WorkbookItem(project.id)
        new_workbook.show_tabs = True
        new_workbook = server_object.workbooks.publish(new_workbook, fname, server_object.PublishMode.Overwrite)
        print("Workbook published. ID: {0}".format(new_workbook.id))


if __name__ == "__main__":
    main()
