DROP USER IF EXISTS 'crmuser'@'localhost';
DROP USER IF EXISTS 'crmuser'@'%';
CREATE USER 'crmuser'@'localhost' IDENTIFIED WITH mysql_native_password BY 'SenhaForte@2025';
CREATE USER 'crmuser'@'%' IDENTIFIED WITH mysql_native_password BY 'SenhaForte@2025';
GRANT ALL PRIVILEGES ON tiextremo_crm.* TO 'crmuser'@'localhost';
GRANT ALL PRIVILEGES ON tiextremo_crm.* TO 'crmuser'@'%';
FLUSH PRIVILEGES;
