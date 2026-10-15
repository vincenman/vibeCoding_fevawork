Write the python script which perform the following task:

Input file:

Folder name of the MD file: location of the folder name with the MD files

 location and name of the MD files (User input which are specified at the beginning of the python script

The systsme prompt: which indicate the prompt which is used to extract the information from the input MD file

location and name of the exported excel file

Telegram bot token: The token of the telegram bot

Telegram Chat ID: The Chat ID of the telegram bot

Data processing:

The fields which are specified in the prompt will be extract using the LLM (the credentials specified in .env file)

The result will be saved as excel file with the first row as the colum name and the second row being the extracted data

After the excel file is ready send it out via telegram 

Use python-telegram-bot for the python library.

Exception handling:

If telegram bot is not working (due to missing token or chat ID) skip the telegram sending and continue the process without generated execution error.