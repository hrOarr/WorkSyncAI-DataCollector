"""
Tech stack detection module for WorkSyncAI Agent
"""

import logging
import os
import re
from typing import Dict, Set, Optional, List
from datetime import datetime
import psutil
from Xlib import display, X
from Xlib.error import DisplayError

# Configure module logger
logger = logging.getLogger(__name__)

# Tech stack patterns and their associated domains
TECH_PATTERNS = {
    # Programming Languages
    'python': {
        'patterns': [r'\.py$', r'python', r'pip', r'django', r'flask', r'fastapi'],
        'domain': 'Python Development'
    },
    'javascript': {
        'patterns': [r'\.js$', r'\.jsx$', r'node', r'npm', r'yarn', r'react', r'angular', r'vue'],
        'domain': 'JavaScript Development'
    },
    'java': {
        'patterns': [r'\.java$', r'\.jar$', r'maven', r'gradle', r'spring', r'intellij'],
        'domain': 'Java Development'
    },
    'csharp': {
        'patterns': [r'\.cs$', r'\.net', r'visual studio', r'dotnet', r'csharp'],
        'domain': '.NET Development'
    },

    # Web Technologies
    'frontend': {
        'patterns': [r'\.html$', r'\.css$', r'\.scss$', r'\.sass$', r'webpack', r'vite'],
        'domain': 'Frontend Development'
    },
    'react': {
        'patterns': [r'react', r'next\.js', r'create-react-app', r'\.jsx$', r'\.tsx$'],
        'domain': 'React Development'
    },
    'angular': {
        'patterns': [r'angular', r'ng serve', r'ng build', r'\.ts$'],
        'domain': 'Angular Development'
    },

    # Backend Technologies
    'nodejs': {
        'patterns': [r'node', r'express', r'nestjs', r'package\.json'],
        'domain': 'Node.js Development'
    },
    'django': {
        'patterns': [r'django', r'manage\.py', r'wsgi', r'asgi'],
        'domain': 'Django Development'
    },
    'spring': {
        'patterns': [r'spring boot', r'application\.properties', r'application\.yml'],
        'domain': 'Spring Development'
    },

    # Databases
    'sql': {
        'patterns': [r'mysql', r'postgresql', r'sql server', r'oracle', r'\.sql$'],
        'domain': 'SQL Development'
    },
    'nosql': {
        'patterns': [r'mongodb', r'mongoose', r'redis', r'elasticsearch', r'dynamodb'],
        'domain': 'NoSQL Development'
    },

    # Mobile Development
    'android': {
        'patterns': [r'android studio', r'\.kt$', r'\.java$', r'gradle', r'adb'],
        'domain': 'Android Development'
    },
    'ios': {
        'patterns': [r'xcode', r'\.swift$', r'\.xcodeproj$', r'cocoapods'],
        'domain': 'iOS Development'
    },

    # DevOps & Cloud
    'devops': {
        'patterns': [r'docker', r'kubernetes', r'jenkins', r'gitlab-ci', r'\.yml$'],
        'domain': 'DevOps'
    },
    'aws': {
        'patterns': [r'aws', r'amazon', r's3', r'ec2', r'lambda'],
        'domain': 'AWS Cloud'
    },

    # Data Science
    'datascience': {
        'patterns': [r'jupyter', r'pandas', r'numpy', r'tensorflow', r'pytorch'],
        'domain': 'Data Science'
    }
}

class TechDetector:
    """Detects technology stacks being used"""

    def __init__(self):
        """Initialize the tech detector"""
        self.active_techs: Set[str] = set()
        self.last_detection_time: float = 0
        self.detection_interval: int = 60  # Check every minute
        self.tech_patterns = {
            tech: [re.compile(pattern, re.IGNORECASE)
                   for pattern in info['patterns']]
            for tech, info in TECH_PATTERNS.items()
        }
        self.display = None
        try:
            self.display = display.Display()
            logger.info("Connected to X display")
        except DisplayError as e:
            logger.error(f"Failed to connect to X display: {str(e)}")

    def _get_active_window_title(self) -> Optional[str]:
        """
        Get active window title using Xlib

        Returns:
            Optional[str]: Active window title or None
        """
        try:
            if not self.display:
                return None

            root = self.display.screen().root
            active_window = root.get_full_property(
                self.display.intern_atom('_NET_ACTIVE_WINDOW'),
                X.AnyPropertyType
            )

            if not active_window:
                return None

            window_id = active_window.value[0]
            window = self.display.create_resource_object('window', window_id)

            # Get window name
            window_name = window.get_full_property(
                self.display.intern_atom('_NET_WM_NAME'),
                X.AnyPropertyType
            )

            # Fallback to WM_NAME if _NET_WM_NAME not available
            if not window_name:
                window_name = window.get_full_property(
                    X.XA_WM_NAME,
                    X.AnyPropertyType
                )

            if window_name:
                return window_name.value.decode('utf-8')

            return None

        except Exception as e:
            logger.error(f"Error getting active window title: {str(e)}")
            return None

    def _get_all_window_titles(self) -> List[str]:
        """
        Get all window titles using Xlib

        Returns:
            List[str]: List of window titles
        """
        titles = []
        try:
            if not self.display:
                return titles

            root = self.display.screen().root
            client_list = root.get_full_property(
                self.display.intern_atom('_NET_CLIENT_LIST'),
                X.AnyPropertyType
            )

            if not client_list:
                return titles

            for window_id in client_list.value:
                window = self.display.create_resource_object('window', window_id)

                # Get window name
                window_name = window.get_full_property(
                    self.display.intern_atom('_NET_WM_NAME'),
                    X.AnyPropertyType
                )

                # Fallback to WM_NAME
                if not window_name:
                    window_name = window.get_full_property(
                        X.XA_WM_NAME,
                        X.AnyPropertyType
                    )

                if window_name:
                    title = window_name.value.decode('utf-8')
                    titles.append(title)

            return titles

        except Exception as e:
            logger.error(f"Error getting window titles: {str(e)}")
            return titles

    def _check_window_title(self, title: str) -> List[str]:
        """
        Check window title for tech stack indicators

        Args:
            title (str): Window title to check

        Returns:
            List[str]: List of detected technologies
        """
        detected = set()
        for tech, patterns in self.tech_patterns.items():
            if any(pattern.search(title) for pattern in patterns):
                detected.add(tech)
        return list(detected)

    def _check_active_files(self) -> List[str]:
        """
        Check currently open files for tech stack indicators

        Returns:
            List[str]: List of detected technologies
        """
        detected = set()
        try:
            # Get all window titles
            titles = self._get_all_window_titles()

            for title in titles:
                # Check window title
                detected.update(self._check_window_title(title))

                # Check if it's a known IDE or text editor
                if any(editor in title.lower()
                       for editor in ['code', 'sublime', 'atom', 'notepad++',
                                      'pycharm', 'intellij', 'eclipse']):
                    # If it's an IDE, the title might contain the file being edited
                    file_patterns = [
                        r'\.([a-zA-Z0-9]+)$',  # File extensions
                        r'([a-zA-Z0-9]+)\s+-\s',  # Common IDE title patterns
                    ]

                    for pattern in file_patterns:
                        matches = re.findall(pattern, title)
                        for match in matches:
                            # Check the extension or name against tech patterns
                            for tech, patterns in self.tech_patterns.items():
                                if any(p.search(match) for p in patterns):
                                    detected.add(tech)

        except Exception as e:
            logger.error(f"Error checking active files: {str(e)}")

        return list(detected)

    def _check_running_processes(self) -> List[str]:
        """
        Check running processes for tech stack indicators

        Returns:
            List[str]: List of detected technologies
        """
        detected = set()
        try:
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    proc_info = proc.info
                    name = proc_info['name'].lower() if proc_info['name'] else ''
                    cmdline = ' '.join(proc_info['cmdline']).lower() if proc_info['cmdline'] else ''

                    # Check process name and command line
                    for tech, patterns in self.tech_patterns.items():
                        if any(pattern.search(name) or pattern.search(cmdline)
                               for pattern in patterns):
                            detected.add(tech)

                except (psutil.NoSuchProcess, psutil.AccessDenied,
                        psutil.ZombieProcess):
                    continue

        except Exception as e:
            logger.error(f"Error checking processes: {str(e)}")

        return list(detected)

    def detect_technologies(self, db):
        """
        Detect currently used technology stack

        Args:
            employee_id (str): Employee identifier
            pc_id (str): PC identifier

        Returns:
            Optional[TechStackEvent]: Tech stack event if changes detected
        """
        current_time = datetime.now().timestamp()

        # Only check if enough time has passed
        if current_time - self.last_detection_time < self.detection_interval:
            return None

        self.last_detection_time = current_time

        try:
            # Detect technologies from different sources
            detected_techs = set()

            # Check active window
            active_title = self._get_active_window_title()
            if active_title:
                detected_techs.update(self._check_window_title(active_title))

            # Check all windows
            detected_techs.update(self._check_active_files())

            # Check processes
            detected_techs.update(self._check_running_processes())

            # If we detected new technologies
            if detected_techs != self.active_techs:
                # Get the primary domain based on detected technologies
                domains = set()
                for tech in detected_techs:
                    if tech in TECH_PATTERNS:
                        domains.add(TECH_PATTERNS[tech]['domain'])

                # Update active technologies
                self.active_techs = detected_techs
                
                print(','.join(sorted(detected_techs)))

                # Create event
                # return TechStackEvent(
                #     employee_id=employee_id,
                #     pc_id=pc_id,
                #     names=','.join(sorted(detected_techs)),
                #     domain=','.join(sorted(domains)),
                #     description="Tech stack change detected",
                #     metadata={
                #         'detection_time': datetime.utcnow().isoformat(),
                #         'technologies': list(detected_techs),
                #         'domains': list(domains)
                #     }
                # )

        except Exception as e:
            logger.error(f"Error detecting tech stack: {str(e)}")

        return None
