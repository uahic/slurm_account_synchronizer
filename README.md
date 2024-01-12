# About
This tool helps synchronizing users from UNIX user groups with SLURM 'associations', which are tuples of (user, account, partition, cluster) with SLURM's database. 


# accounts.yml
You need to define general accounts (SLURM's unit of accounting for statistics of resource usage etc.) and assign groups to them. The tool will then expand the group names by the information it gets by running ``` getent groups ``` and creates for each implicitly specified user the required SLURM associations. 

### Group operations
You can take any valid unix group and perform one or multiple of the following operations which are performed in the order as written:
- UNION of multiple groups (just specifiy multiple groups to achieve this)
- add_users to add single user names
- exclude_users to remove single user names
- whitelist to perform, given the result of the previous operations, a set-intersection with the specified groups. This is helpful to generally filter out smaller subset of a bigger group

Example:
```
declared_groups: 
  white_knights: 
    groups:
      - ids
    whitelist:
      - slurm_users
    add_users:
      - lanzelot
    exclude_users:
      - darth_vader

```
The virtual group 'white_knights' can further be used in the associations section, as if it was a regular unix group.

## Default Accounts
Each specified user (either by name, by groups or set-operations on multiple groups) will get an user-account (accountname=username) and this will also be the defaultaccount (SLURM requires each user to have one) unless specified otherwise in the defaults section in the accounts.yml. o

As one user can be contained in multiple associations/groups, this tool decides which account to use as a default in the following order according to the accounts.yml:

1. defaults/users/<username> (if defined)
2. defaults/groups/<group_name>/account/<account_name>. As there could be multiple matches, we simply choose the first one in the array where a specific user is member of (the group <group_name>). 

## Full Specification by example

```
declared_groups: # Optional
  my_virtual_group:
    groups:
      - <group_name_1> 
    whitelist:
      - <group_name_2> 
      - <group_name_3> 
    add_users:
      - <user_name_1>
      - <user_name_2>
    exclude_users:
      - <user_name_3>
    

defaults:
  cluster: ids-tks-gpu-cluster # Do not change! Required! Has to match entry inslurm.conf
  organization: fzi # Required but arbitrary
  groups: #Optional
    my_virtual_group:
      account: platsch
  users: #Optional
    <some_user_name>:
       account: tks

accounts: # Required, be hierarchical by specifying a parent
  cool_kids:
    description: # Required
    parent: 'root' # Optional, default is always 'root'
    <... optional limits, see SLURMs documentation>
  tks:
    description: General TKS account
    parent: cool_kids
    fairshare: 1 # Optional
    <... optional limits, see SLURMs documentation>
  ids:
    description: General IDS account
    parent: cool_kids
    fairshare: 5 # Optional
  blubb: # has no parent => SLURM's top-level account 'root' is parent
    description: General IDS account
    fairshare: 3 # Optional
  platsch:
    description: Yeah...

associations:
  <some_association_name>:
    account: blubb
    groups:
      - my_virtual_group # virtual group
      - tks              # actual unix group
    fairshare: 55 # optional
    <... optional limits, see SLURMs documentation>

```

# Usage
By default the accounts.yml has to reside in the same folder as the main.py.
If users have been added or removed on your machine, you need to re-run this script again to inform SLURM about the differences. 

run ``` python main.py ``` to do a dry run (which is the default)

Options:
- '-e' or '--execute' to let the scripts do the SLURM calls.
- '-f' or '--file' to specify the full path of your config YAML file.


### LICENSE
MS: To be discussed, this work has been started/created mainly (3/4 of the consumed time) as a private project and I'd like to open-source it under the Apache 2.0 license at some point. Similar tools do exist but I have not found one that has all the features as contained in this project.
