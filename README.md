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

# Usage

run ``` python main.py ``` to do a dry run (which is the default)

Options:
- '-e' or '--execute' to let the scripts do the SLURM calls.
