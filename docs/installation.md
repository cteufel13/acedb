# Installation and Setup

## 1. Installation

Currently `acedb` is supported in python > 3.11. It can be easily installed like this:

```bash
pip install acedb
```

## 2. Setup

To setup the different clients and components you need to run the following CLI commands:


### 2.1 Database Information
Login to the PostgreSQL database and save configuration.
``` bash
acedb login  
```
This command will prompt you for 
- Host address
- Port number
- Database name
- Username
- Password

This command will: 
1. Test connection to verify credentials
2. Save the data locally so that it is loaded in each session.

#### Example:
```bash
$ acedb login
Enter the host: localhost
Enter the port: 5432
Enter the database name: financial_database
Enter the username: analyst
Enter the password: ****

Success: Database connection established.
Success: Login credentials saved.
```

### 2.2 Databento Key
This command will promp you to enter your Databento API key as found here as found [here](https://databento.com/portal/keys).
```bash
$ acedb dbn-login
Enter your Databento API key: db-**********
Success: Databento API key configured
``` 



### 2.3 Fred API key
This prompts you to enter your FRED API key as found [here](https://fredaccount.stlouisfed.org/apikeys).
```bash
$ acedb fred-login
Enter your FRED API key: ***********
Success: FRED API key configured.
```



## Further Information:

For further detail about the CLI take a look at the [CLI docs](CLI.md)