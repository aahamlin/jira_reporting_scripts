# Jira Reporting Scripts (0.99.22)

To address some of the deficiencies in Jira reporting, here is a small command line tool to 
exercise the [Jira REST API](https://docs.atlassian.com/jira/REST/cloud/) to retrieve information about Stories,
including story points and iterations and export into CSV format. This enables building better reports in Excel.

MacOS:   Python 2.7 & 3.6 (tested)

Windows: Python 3.6 (tested), 2.7 (not tested)

You may want to view/download the [Quickstart Guide](doc/Quickstart.docx).

## Setup

Initial configuration uses the dummy account name, yourusername.atlassian.net. This is stored in the `defaults.ini`
file contained within the module itself. At a minimum users should create a user preference configuration at `$HOME/.qjira.ini` setting the `base_url` value in the `jira` section. Users can also customize queries, switch between effort schemes (story points versus time-based), and customize the set of state transitions reported by the `cycletime` command.

An example custom configuration:
```
[jira]
base_url = http://nagtswjira:8080
default_effort_engine = engine_time

[site_transitions]
lead_begin = .+_to_Ready,lt,False
cycle_begin = .+_to_WorkInProgress,lt,True
cycle_mid = .+_to_WorkInProgress,gt,False
sub_cycle1_begin = from_WorkInProgress_to_WorkCompleted,gt,False
sub_cycle1_end = from_WorkCompleted_to_Resolved,gt,False
sub_cycle2_begin = from_Resolved_to_VerifyingInProgress,gt,True
sub_cycle2_end = from_VerifyingInProgress_to_Resolved,gt,False
cycle_end = (?!from_WorkCompleted).+_to_Resolved,gt,False
lead_end = .+_to_Resolved,gt,False

[cycletime]
query = issuetype in ("new feature", improvement, bug) AND status in (Resolved, Closed) AND resolution = Verified
transitions = site_transitions
```


**IMPORTANT NOTES**

Installation requires setuptools >= 20.5.

> Mac installation of latest setuptools will require installing to the user library.
>
> `$ pip install --user setuptools`

The usage interface has changed. Command names are now full words. Global output options, such as `-o outfile`, follow the command names.

> For example, the summary command `s` is now `summary` as shown here:
>
> `$ qjira summary -o summary-iiqcb.csv -f 7.3 IIQCB`


## New Features

The configuration of commands are being extracted to configuration file, `defaults.ini`. Users can override by creating `$HOME/.qjira.ini`.

Added new command `myworklog` that lists all work logged for the current user.

Added new command `qjira_dump` that will list a single item including all fields in necessary format to use as configuration data, such as headers.

### Summary defaults to HTML output

The `summary` command will not produce an HTML fragment document by default. This can be copy-pasted into a Harbor document, using Harbor's
 &lt;html&gt; editor. You can access the old CSV behavior using the `--csv` parameter.

### OS credential storage

Added the `keyring` module, enabling storage of your Jira credentials in your OSes keychain or credential vault. MacOS and Windows are supported. The script may prompt that Python wants to access `qjira-sp` in your credential store. You should allow it always, unless you really like typing your password over and over again.

### JQL query

Added the `jql` command, print output of any provided JQL query.

### Technical Debt

Added the `debt` command, prints a table of story points versus bug points including percentage of tech debt (bugs) completed per project.

### Bug Backlog

Added the bug `backlog` command, prints all bugs by fix version.

# Commands

```
usage: qjira [-h] [-b URL] [-u USER] [-w PWD] [-d] [-1]
             {cycletime,velocity,summary,debt,backlog,worklog,jql} ...

Exports data from Jira to CSV format

optional arguments:
  -h, --help            show this help message and exit
  -b URL, --base URL    Jira Cloud base URL [default:
                        https://yourusername.atlassian.net]
  -u USER, --user USER  Username, if blank will use logged on user
  -w PWD, --password PWD
                        Password (insecure), if blank will prommpt
  -d, --debug           Debug level
  -1, --one-shot        Process single record only

Available commands:
  {cycletime,velocity,summary,debt,backlog,worklog,jql}
                        Available commands to process data
    cycletime           Produce cycletime data
    velocity            Produce velocity data
    summary             Produce summary report
    debt                Produce tech debt report
    backlog             Query bug backlog by fixVersion
    worklog             Query worklog entries
    jql                 Query using JQL
```

## Summary

Prints backlog summary and documentation links for stories in a project using Excel formulas. Note: In order to
format correctly in a Harbor document import the CSV file into Excel using comma delimiters, then copy-paste the
table into your Harbor document.

```
usage: qjira summary [-h] [-o [FILENAME]] [--no-progress] [--encoding ENC]
                     [--delimiter CHAR] [-A] [-f VERSION] [--mark-new]
                     project [project ...]

positional arguments:
  project               Project name

optional arguments:
  -h, --help            show this help message and exit
  -o [FILENAME], --outfile [FILENAME]
                        Output file (.csv) [default: stdout]
  --no-progress         Hide data download progress
  --encoding ENC        Specify an output encoding. In Python 2.x, only
                        default ASCII is supported.
  --delimiter CHAR      Specify a CSV delimiter [default: comma]. For bash
                        support escape the character with $, such as $'\t'
  -A, --all-fields      Extract all "navigable" fields in Jira,
                        [fields=*navigable]
  -f VERSION, --fix-version VERSION
                        Restrict search to fixVersion(s)
  --mark-new, -N        Mark docs linked within past 2 weeks
  --csv                 Output CSV rather than HTML Fragments
```

## Velocity

Calculate the story points planned, completed, and carried over for every sprint associated with an issue.

Issues (story or bug) that have not been assigned at least one sprint will not be reported on (because velocity only makes sense in the context of a sprint(s).

Sprints without defined start and end dates will not be reported.

```
usage: qjira velocity [-h] [-o [FILENAME]] [--no-progress] [--encoding ENC]
                      [--delimiter CHAR] [-A] [-f VERSION] [--include-bugs]
                      [--forecast] [--raw] [--filter-by-date START]
                      project [project ...]

positional arguments:
  project               Project name

optional arguments:
  -h, --help            show this help message and exit
  -o [FILENAME], --outfile [FILENAME]
                        Output file (.csv) [default: stdout]
  --no-progress         Hide data download progress
  --encoding ENC        Specify an output encoding. In Python 2.x, only
                        default ASCII is supported.
  --delimiter CHAR      Specify a CSV delimiter [default: comma]. For bash
                        support escape the character with $, such as $'\t'
  -A, --all-fields      Extract all "navigable" fields in Jira,
                        [fields=*navigable]
  -f VERSION, --fix-version VERSION
                        Restrict search to fixVersion(s)
  --include-bugs, -B    Include bugs in velocity calculation
  --forecast, -F        Include future sprints in velocity calculation
  --raw, -R             Output all rows instead of summary by sprint name.
  --filter-by-date START
                        Filter sprints starting earlier than START date.
```

## Cycle Time

Calculate the days from being moved to In Progress by devs to being closed by testers.

Limitations: 

  * This does not subtract time for an issue moved from In Progress back to Open. 

  * This does not record separate values for bugs being dev complete 'Resolved' and being test complete 'Closed'.


```
usage: qjira cycletime [-h] [-o [FILENAME]] [--no-progress] [--encoding ENC]
                       [--delimiter CHAR] [-A] [-f VERSION]
                       project [project ...]

positional arguments:
  project               Project name

optional arguments:
  -h, --help            show this help message and exit
  -o [FILENAME], --outfile [FILENAME]
                        Output file (.csv) [default: stdout]
  --no-progress         Hide data download progress
  --encoding ENC        Specify an output encoding. In Python 2.x, only
                        default ASCII is supported.
  --delimiter CHAR      Specify a CSV delimiter [default: comma]. For bash
                        support escape the character with $, such as $'\t'
  -A, --all-fields      Extract all "navigable" fields in Jira,
                        [fields=*navigable]
  -f VERSION, --fix-version VERSION
                        Restrict search to fixVersion(s)
```

## Tech Debt

Generate table of project_name, bug_points, story_points, & tech_debt percentage.

```
usage: qjira debt [-h] [-o [FILENAME]] [--no-progress] [--encoding ENC]
                  [--delimiter CHAR] [-A] [-f VERSION]
                  project [project ...]

positional arguments:
  project               Project name

optional arguments:
  -h, --help            show this help message and exit
  -o [FILENAME], --outfile [FILENAME]
                        Output file (.csv) [default: stdout]
  --no-progress         Hide data download progress
  --encoding ENC        Specify an output encoding. In Python 2.x, only
                        default ASCII is supported.
  --delimiter CHAR      Specify a CSV delimiter [default: comma]. For bash
                        support escape the character with $, such as $'\t'
  -A, --all-fields      Extract all "navigable" fields in Jira,
                        [fields=*navigable]
  -f VERSION, --fix-version VERSION
                        Restrict search to fixVersion(s)
```

## Bug Backlog

Prints backlog summary of bugs by fix version. This adds a row per fix version for filtering in Excel.

```
usage: qjira backlog [-h] [-o [FILENAME]] [--no-progress] [--encoding ENC]
                     [--delimiter CHAR] [-A] [-f VERSION]
                     project [project ...]

positional arguments:
  project               Project name

optional arguments:
  -h, --help            show this help message and exit
  -o [FILENAME], --outfile [FILENAME]
                        Output file (.csv) [default: stdout]
  --no-progress         Hide data download progress
  --encoding ENC        Specify an output encoding. In Python 2.x, only
                        default ASCII is supported.
  --delimiter CHAR      Specify a CSV delimiter [default: comma]. For bash
                        support escape the character with $, such as $'\t'
  -A, --all-fields      Extract all "navigable" fields in Jira,
                        [fields=*navigable]
  -f VERSION, --fix-version VERSION
                        Restrict search to fixVersion(s)
```

## Worklog

Downloads records of time spent logs by worklogAuthor.

```
usage: qjira worklog [-h] [-o [FILENAME]] [--no-progress] [--encoding ENC]
                     [--delimiter CHAR] [-A] [-S yyyy/mm/dd] [-E yyyy/mm/dd]
                     [--authors-only] [--total] [-G GROUP_BY]
                     [AUTHOR [AUTHOR ...]]

positional arguments:
  AUTHOR                Author name(s)

optional arguments:
  -h, --help            show this help message and exit
  -o [FILENAME], --outfile [FILENAME]
                        Output file (.csv) [default: stdout]
  --no-progress         Hide data download progress
  --encoding ENC        Specify an output encoding. In Python 2.x, only
                        default ASCII is supported.
  --delimiter CHAR      Specify a CSV delimiter [default: comma]. For bash
                        support escape the character with $, such as $'\t'
  -A, --all-fields      Extract all "navigable" fields in Jira,
                        [fields=*navigable]
  -S yyyy/mm/dd, --start-date yyyy/mm/dd
                        Exclude worklogDate before start date
  -E yyyy/mm/dd, --end-date yyyy/mm/dd
                        Exclude worklogDate after end date
  --authors-only        Restrict listings to authors provided.
  --total               Include total days per author
  -G GROUP_BY, --group-by GROUP_BY
                        Group results by an arbitrary (existing) column, e.g.
                        project_name.
```

## JQL Query

Converts any freeform jql queries to CSV.

```
usage: qjira jql [-h] [-o [FILENAME]] [--no-progress] [--encoding ENC]
                 [--delimiter CHAR] [-A] [--add-field NAME]
                 [--add-column NAME]
                 jql

positional arguments:
  jql                   JQL statement

optional arguments:
  -h, --help            show this help message and exit
  -o [FILENAME], --outfile [FILENAME]
                        Output file (.csv) [default: stdout]
  --no-progress         Hide data download progress
  --encoding ENC        Specify an output encoding. In Python 2.x, only
                        default ASCII is supported.
  --delimiter CHAR      Specify a CSV delimiter [default: comma]. For bash
                        support escape the character with $, such as $'\t'
  -A, --all-fields      Extract all "navigable" fields in Jira,
                        [fields=*navigable]
  --add-field NAME, -f NAME
                        Add field(s) to Jira request
  --add-column NAME, -c NAME
                        Add column(s) to CSV output
```

# Future enhancements

  *  Add argument including set of default IIQ project names 

  *  Unify sprint names & date ranges

# Installation

  * Uses setuptools for installation. On MacOS, install requires root permission via `sudo`. 

`$ pip install git+https://github.com/aahamlin/jira_reporting_scripts.git`

  * Or, install as user (requires updating your $PATH)
  
`$ pip install --user git+https://github.com/aahamlin/jira_reporting_scripts.git`

# Command line usage

  * View help message
  
`$ qjira -h`
`$ qjira {command} -h`

  * Produce velocity data
  
`$ qjira velocity -f 7.2 IIQHH`
  
  * Produce velocity forecast including bug points
  
`$qjira velocity -f 7.3 -F -B IIQCB`
  
  * Produce cycletime data
  
`$ qjira cycletime -f 7.2 IIQCB`

  * Produce summary report

`$ qjira summary -f 7.2 IIQCB`

  * Produce technical debt report
  
`$ qjira debt -f 7.2 IIQCB`

  * Produce bug backlog listing
  
`$ qjira backlog -f 7.3 IIQETN`

  * Multiple projects and output CSV file
  
`$ qjira velocity -o velocity.csv IIQCB IIQHH`

  * Print to console with a tab delimiter
  
`$ qjira velocity --delimiter=$'\t' -f 7.3 IIQCB`

# Dependencies

  * requests
  
  * python-dateutil
  
  * keyring
  
  * six

# Development

Use python virtualenv to isolate the required libraries. `$ source bin/activate`

Update dependencies, `$ make init`

Clean build tree, `$ make clean`

Package distribution, `$ make dist` or `$ make dist-all`

Run all unit tests, `$ make test`

Run set of functional tests, `$ ./tests/qjira_func_test.sh`

Run from development virtualenv, `$ python -mqjira -h`

Exit the virtualenv, `$ deactivate`

Basic make commands: 

  * Initialize the project dependencies

`$ make init`

  * Run the unit tests in your current Python environment

`$ make test`

  * Run the unit tests in both python 2.7 and python 3 environments using `virtualenv`
  
`$ make test-all`

  * Clean the binary and cached output
  
`$ make clean`

  
