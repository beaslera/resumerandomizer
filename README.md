Resume Randomizer
=================

Resume Randomizer randomly combines text fragments, and was created to assist correspondence studies.

The Resume Randomizer program comes in two parts: the webpage (resume-randomizer.html) allows an experimenter to define and input the characteristics of the resume or correspondence general template, while the python script file (resume-randomizer.py) generates resumes from those templates.  Here we discuss use of the program in creating resumes, but the program is general enough to be used for other text randomization tasks such as creating cover letters or creating randomized software or HTML pages.

Motivation for use of this software is discussed in:
[Lahey, Joanna and Beasley, Ryan A., Computerizing Audit Studies (July 1, 2007).](http://ssrn.com/abstract=1001038) http://dx.doi.org/10.2139/ssrn.1001038

****************************************************************

Overview:
---------

The included software is intended to assist researchers in performing large-scale resume audit studies by using computer-generated randomization to assign characteristics to resumes.

The experimenter first uses the webpage interface (i.e., checkboxes, buttons, and text entry areas) to create the template, which is effectively an outline for the resumes to be generated.  Each point in the outline determines the probability that text in its sub-points (i.e., characteristics) will get output to the resume files.  Outline points can be set to repeat a specified number of times, useful for generating work history by repeatedly choosing between possibilities for previous jobs.  Furthermore, the outline can be set up for matched resumes, such as for a matched-pairs audit (though the program is not limited to matching only two resumes at a time).  Specifically, points can be set either so that all of the matched resumes will choose the same sub-point, or so that they will all choose different sub-points.  Combining the repetition and matching settings can improve the above example by forcing all the resume files to choose the same sub-point (a matched characteristic).  That sub-point could contain text listing a specific previous job, or it could have sub-points and force matched files to choose different sub-points all describing functionally equivalent jobs (to keep the resumes from looking like copies).  The program is provided with example templates that demonstrate such uses.  The webpage explains template creation in further detail.

Once the template has been created using the webpage, the python script (resume-randomizer.py) can be run any number of times.  Each time it is run, the experimenter can instruct it to generate any number of resumes, either not matched or matched within groups of any size.  Along with each resume, the program creates a record of the random choices that were made in the creation of that resume, sufficient for exact re-creation of that resume for use in analysis.

****************************************************************

Instructions:
-------------

1. Place all of the files in the same folder.

2. The webpage consists of one html file.  Load "resume-randomizer.html" into your web browser.  The webpage has been tested and works in Firefox, Chrome, Safari, Internet Explorer, and Microsoft Edge.  The webpage contains further explanation and instructions.

3. Once one or more template files have been generated, use Python 3.11 or later to run the python script "resume-randomizer.py" to generate resumes.  Four sample template files are provided to demonstrate the use of the program: "example_cover_letter_template.rtf", "example_resume_template.rtf", "example_resume_template_with_fragments.rtf", and "example_cyrillic_template.rtf".

****************************************************************

Creating a Windows executable:
-------------

To create an executable file,

1. Install Anaconda Python.

2. Ensure that resume-randomizer.py will run.

3. conda install pyinstaller.

4. pyinstaller --onefile resume-randomizer.py


That will create an executable file that is larger than necessary, e.g., 300MB, so if it is important to reduce the size of the executable:
1. Install a non-Anaconda Python.

2. Create a new virtual environment and activate it.
python -m venv ./pyinstaller_venv

3. Install pandas, chardet, and pyinstaller.
pip install pandas chardet pyinstaller

4. Use that pyinstaller (in the Scripts folder) to create the executable.  This approach generated a 24MB file.
