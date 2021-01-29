"""
CanvasSync by Mathias Perslev
February 2017

--------------------------------------------

course.py, Second level class in hierarchy

The Course class is the second level CanvasEntity object in the folder hierarchy. It inherits from the base CanvasEntity
class and extends its functionality to allow downloading information on Modules listed under the course in the Canvas
system. A Module object is initialized for each module found and appended to a list of children under the
Course object. In addition, the object may initialize and store the AssignemntsFolder object representing the collection
of assignments of the course as well as a single Folder object representing the collection of Folders and Files stored
under the 'Files' section in Canvas.

The Synchronizer class is the parent object.

See developer_info.txt file for more information on the class hierarchy of CanvasEntities objects.

"""

# Future imports
from __future__ import print_function

# Inbuilt modules
import os

# Third party
from six import text_type

# CanvasSync modules
from CanvasSync import constants as CONSTANTS
from CanvasSync.entities.assignments_folder import AssignmentsFolder
from CanvasSync.entities.canvas_entity import CanvasEntity
from CanvasSync.entities.folder import Folder
from CanvasSync.entities.module import Module
from CanvasSync.utilities import helpers
from CanvasSync.utilities.ANSI import ANSI


class Course(CanvasEntity):
    def __init__(self, course_info, parent, settings):
        """
        Constructor method, initializes base CanvasEntity class and adds all children Module objects to the list of children

        course_info   : dict    | A dictionary of information on the Canvas course object
        parent        : object  | The parent object, the Synchronizer object
        """

        self.course_info = course_info

        course_id = self.course_info[CONSTANTS.ID]

        course_name = helpers.get_corrected_name(self.course_info[CONSTANTS.COURSE_CODE].split(";")[-1])

        if settings.use_nicknames:
            course_name = self.course_info[CONSTANTS.NAME]

<<<<<<< HEAD
        course_path = os.path.join(parent.get_path(), course_name)
=======
        course_path = parent.get_path() # + course_name
>>>>>>> 763eeb91d092aaaf225ea46abcfc5dd0a4a0f8c0

        self.to_be_synced = True if course_name in parent.settings.courses_to_sync else False

        # Initialize base class
        CanvasEntity.__init__(self,
                              id_number=course_id,
                              name=course_name,
                              sync_path=course_path,
                              parent=parent,
                              identifier=CONSTANTS.ENTITY_COURSE,
                              folder=self.to_be_synced)

    def __repr__(self):
        """ String representation, overwriting base class method """
        status = ANSI.format(u"[SYNCED]" if self.to_be_synced else u"[SKIPPED]", formatting=u"green" if self.to_be_synced else u"yellow")
        return status + u" " * (7 if self.to_be_synced else 6) + u"|   " + u"\t" * self.indent + u"%s: %s" \
                                                        % (ANSI.format(u"Course", formatting=u"course"), self.name)

    def download_modules(self):
        """ Returns a list of dictionaries representing module objects """
        return self.api.get_modules_in_course(self.id)

    def add_modules(self):
        """ [HIDDEN]  Method that adds all Module objects to the list of Module objects """

        # Download list of dictionaries representing modules and add them all to the list of children
        for position, module_info in enumerate(self.download_modules()):
            module = Module(module_info, position+1, parent=self)
            self.add_child(module)

    def download_assignemtns(self):
        """ Return a list of dictionaries representing assignment objects """
        return self.api.get_assignments_in_course(self.id)

    def add_assignments_folder(self):
        """ Add an AssigmentsFolder object to the children list """

        # Download potential assignments
        assignments_info_list = self.download_assignemtns()

        if len(assignments_info_list) == 0:
            return

        assignments = AssignmentsFolder(assignments_info_list, self)
        self.add_child(assignments)

    def add_files_folder(self):
        """ Add a SubFolder object representing the files folder of the course """

        # The main file folder should always be the first in the list, but is there a better way to get this initial ID
        # than downloading the entire list of folders??
        folders = self.api.get_folders_in_course(self.id)

        main_folder = None
        for folder in folders:
            if folder[u"full_name"] == u"course files":
                main_folder = folder
                break

        # Change name of folder
        # main_folder[u"name"] = u"Other Files"

        # We can just have the course files be place in the course folder
        # instead of putting it in a subfolder called Other Files

        main_folder[u"name"] = self.course_info["name"]

        folder = Folder(main_folder, self)
        self.add_child(folder)

    def walk(self, counter):
        """ Walk by adding all Modules and AssignmentFolder objects to the list of children """

        if not self.to_be_synced:
            return

        if not list(self.settings.modules_settings.values()) == [False, False, False]:
            self.add_modules()

        print(text_type(self))

        # Add an AssignmentsFolder if at least one assignment is found under the course
        self.add_assignments_folder()

        # Add files folder
        self.add_files_folder()

        counter[0] += 1
        for child in self:
            child.walk(counter)

    def sync(self):
        """
        1) Adding all Modules and AssignmentFolder objects to the list of children
        2) Synchronize all children objects
        """
        print(text_type(self))

        if not self.to_be_synced:
            return

        if not list(self.settings.modules_settings.values()) == [False, False, False]:
            self.add_modules()

        if self.settings.sync_assignments:
            # Add an AssignmentsFolder if at least one assignment is found under the course
            self.add_assignments_folder()

        # Add Various Files folder
        self.add_files_folder()

        # sync history
        history_record = dict({
            CONSTANTS.HISTORY_ID: self.get_id(),
            CONSTANTS.HISTORY_PATH: self.get_path(),
            CONSTANTS.HISTORY_TYPE: CONSTANTS.ENTITY_COURSE
        })
        self.synchronizer.history.write_history_record_to_file(history_record)

        for child in self:
            child.sync()

    def show(self):
        """ Show the folder hierarchy by printing every level """
        print(text_type(self))

        for child in self:
            child.show()
