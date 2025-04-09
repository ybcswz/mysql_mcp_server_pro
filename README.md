# mcp_mysql_server

## Introduction
- Added support for STDIO mode and SSE mode
- Added support for multiple SQL execution, separated by ";"
- Added ability to query database table names and fields based on table comments
- Added SQL Execution Plan Analysis
- Added Chinese field to pinyin conversion

## Usage Instructions

### STDIO Mode
- Use src/studio_mcp/operatemysql.py

Add the following content to your mcp client tools, such as cursor, cline, etc.

mcp json as follows:
```
{
  "mcpServers": {
      "operateMysql": {
        "isActive": true,
        "name": "operateMysql",
        "command": "uv",
        "args": [
          "--directory",
          "G:\\python\\mysql_mcp\\src\\studio_mcp",  # Here you need to replace with your project path.
          "run",
          "operatemysql.py"
        ],
        "env": {
          "MYSQL_HOST": "192.168.xxx.xxx",
          "MYSQL_PORT": "3306",
          "MYSQL_USER": "root",
          "MYSQL_PASSWORD": "root",
          "MYSQL_DATABASE": "a_llm"
       }
    }
  }
}    
```
### SSE Mode
- Use src/sse_mcp/operatemysql.py
- Use uv to start the service

Add the following content to your mcp client tools, such as cursor, cline, etc.

mcp json as follows:
```
{
  "mcpServers": {
    "operateMysql": {
      "name": "operateMysql",
      "description": "",
      "isActive": true,
      "baseUrl": "http://localhost:9000/sse"
    }
  }
}
```

Modify the .env file content to modify the database connection information to your database connection information
```
# MySQL database configuration
MYSQL_HOST=192.168.xxx.xxx
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=a_llm
```

Start command
```
# Download dependencies
uv sync

# run 
uv run operatemysql.py
```

## Example
prompt format as follows
```
# Task
    Create an organization structure table, table structure as follows: department name, department number, parent department, whether effective.
# Requirements
 - Table name use t_admin_rms_zzjg,
 - Field requirements: string type uses 'varchar(255)', integer type uses 'int', float type uses 'float', date and time type uses 'datetime', boolean type uses 'boolean', text type uses 'text', large text type uses 'longtext', large integer type uses 'bigint', large float type uses 'double'.
 - Table header needs to add primary key field, serial number XH varchar(255)
 - Table last needs to add fixed fields: creator-CJR varchar(50), creation time-CJSJ datetime, modifier-XGR varchar(50), modification time-XGSJ datetime.
 - Field naming uses tool return content as field naming
 - Common fields need to add indexes
 - Each field needs to add comments, table comments need to be added
 - Generate 5 real data after creation
```

#### Effect picture
![image](https://github.com/user-attachments/assets/e95dc104-4e26-426a-acd4-d3b15ad654f5)

![image](https://github.com/user-attachments/assets/618f610e-5188-4c40-aeaa-cfbe7b0762c3)

![image](https://github.com/user-attachments/assets/4c91c8d1-4a42-41f4-8fe2-e46df0f08daa)

![image](https://github.com/user-attachments/assets/328a2cce-11ac-48f0-818a-1f1d231d7013)

![image](https://github.com/user-attachments/assets/db265aaf-a3e9-41b4-bf7a-235ba34ed4cd)

![image](https://github.com/user-attachments/assets/c67e2948-78af-4c8a-b1ff-6a7172bbb6f8)

![image](https://github.com/user-attachments/assets/9f6215e6-51fc-4e32-9d21-3e19abfa4bc6)

![image](https://github.com/user-attachments/assets/f10fc2b7-ac41-4f2c-a163-c7683bf2fabe)




