#!/usr/bin/env python3

# Importing libraries needed
import os
import subprocess as adbCMD
import time
import difflib
from pprint import pprint
import sys
import filecmp
import re
from datetime import datetime
import smtplib
import ssl
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd # dont forget to <pip install pandas> if not already installed


# Declearing some variables
#timeout_seconds = 4 # This is the time for the logcat function to time out so other processes can continue
output_filename ="logcat_output.txt" # This is the logged data before further cleaning
max_RetryCount = 3
#global idx

# To show start date and time 
start_Time_Date = datetime.now()
print ("Test started at: ", start_Time_Date)


# To check is there is an already saved logcat file and delete it before starting the new test
saved_logcatoutput = 'savedLogs.txt'
check_if_file_exist = os.path.isfile(saved_logcatoutput)
if check_if_file_exist == True:
	os.system('rm -r savedLogs.txt')
time.sleep(1)

# function to handle logging, cleaning and saving of the adb logcat output 
def log_cleaned_and_save_output():
	adbCMD.run("adb logcat -d >> savedLogs.txt", shell=True)
	adbCMD.run("adb logcat -c all", shell=True) # adb command to clear any log file save in the device
#	time.sleep(3)
	adbCMD.run("adb shell input tap 980 130", shell=True) # To cancel the Pass/Fail pop up
	adbCMD.run("adb shell input tap 630 475", shell=True) # To tap the Start button
	time.sleep(9)
	# Capturing the logcat file
	try:
		with open("logcat_output.txt", "w") as output_file:
			adbCMD.run("adb logcat -s HQA -d > logcat_output.txt", shell=True) # This is to get the logs from devices focusing on lines with the PID "HQA"
#			print (f"Logcat output saved to logcat_output")

	#Commands  to handle errors and exceptions and timeout info
	except adbCMD.TimeoutExpired:
		print ("Logcat captured timed out")
	except adbCMD.CalledProcessError as e:
		print (f"Error: {e.returncode}\n{e.stderr}")
	except Exception as e:
		print (f"An error occured: {e}")

#	time.sleep(1)
# Carrying out further  cleaning on the logged file to enable easier comparison with the reference file
	# variables to temporalily save and open the text files
	loggedFile = "logcat_output.txt"
	semiCleanedFile = "semi_cleaned.txt"
	finalCleanedFile = "cleaned_file.txt"
	#comparedFile = "Captured.txt"


	# List of unwanted write ups in the logcat file
	list_to_delete = ["--------- beginning of main", "--------- beginning of system"]

	fileIN = open(loggedFile)
	fileOUT = open(semiCleanedFile, "w")
	for line in fileIN:
		for word in list_to_delete:
			line = line.replace(word, "") # this is replacing those unwanted writes ups with empty spaces
		fileOUT.write(line)
	fileIN.close()
	fileOUT.close()
#	time.sleep(1)
	os.system("sed -i '/./,$!d' semi_cleaned.txt") # To take away the empty first lines created by deleteing unwanted write ups
#	time.sleep(1)
	os.system("sed 's/...............................//' semi_cleaned.txt > cleaned_file.txt") #deleting the date and time stamps for comparison sake.

	# This is to remove all ANSI escape codes introduced by logcat in the logged file
	# Define a pattern to match ANSI escape codes and non-alphanumeric characters
	removeESC_code = re.compile(r'\x1b\[.*?m|[^a-zA-Z0-9\s]')
	# Read the content of the file and cleaned each line
	cleaned_lines = []
	with open('cleaned_file.txt', 'r') as file1:
		for line  in file1:
			cleaned_line = removeESC_code.sub('', line)
			cleaned_lines.append(cleaned_line)

	# Create or write the cleaned file with the cleaned lines
	with open('final_output.txt', 'w') as file2:
		file2.writelines(cleaned_lines)


# Comparing the cleaned file with the Reference file
#	time.sleep(1)
	with open('Reference.txt') as referencer: # The file we are mking reference to
		line1 = referencer.readlines()

	with open('final_output.txt') as referencee: # the cleaned file 
		line2 = referencee.readlines()

	# This is to instantiate a Differ object
	differ = difflib.Differ()
	#The results are saved as a list
	diff = list(differ.compare(line1, line2))

# A for loop ro create a line numbering system and at the same tim loop through the lines of each file whiel comparing them
# idx gives the line numbering and with that we can locate the exact line the differnce occured
	for idx, line in enumerate(diff, start=1):
		if line.startswith('_ '): # This is for the the reference file 
			print (f"Differnce in line {idx} of {'referencer'}: {line[2:]}")
		elif line.startswith('+ '): # This is for the captured and cleaned file to be comapared
			print (f"Difference in line {idx} of {'referencee'}: {line[2:]}")
			if idx == 4:
				print ("PSCR on Fail and Rerunung Test....")
			elif idx == 6:
				print ("PSCR Read Fail, Reruninig Test....")
#				log_cleaned_and_save_output()
			elif idx == 8:
				print ("PSCR off Fail, Reruninig Test.....")

# A pretty print to see how the comparison is being done
#	pprint(diff)



# Function to handle email sending using custom made email address via gmail server 
def emailSender():

	# Define email sender and reciver details
	email_sender = 'vfi.lds.robotics@gmail.com'
	email_passwd = 'gxig ofsj xqrx uyph'
	#email_receiver = 'emmanuel.adolphus@verifone.com'

	# to set the subject and body of the email
	subject = 'Robotics Test'
	body = """
	Ooops! Test failed, please see attached result and logged file
	"""

	# Reading the CSV file containing the email addresses to sendt notification to and the name of files to attach
	csv_path = 'emailAddressDIR.csv'
	email_dir = pd.read_csv(csv_path)

        # Looping through the csv file and sending the emails accordingly
	for index, row in email_dir.iterrows():
		email_receiver = row['Receiver']
		attachment_file_name = row['Attachment']

		# Instantiate an email object
		errEmail = EmailMessage()
		errEmail['From'] = email_sender
		errEmail['To'] = email_receiver
		errEmail['Subject'] = subject
		errEmail.set_content(body)

		# Make the message multipath
		errEmail.add_alternative(body, subtype='html')

		# attach the file to be sent
		with open(attachment_file_name, 'r') as attachment_file:
			file_data = attachment_file.read()
			file_name = attachment_file_name.split("/")[-1]


		attachment = MIMEBase('application', 'octet-stream')
		attachment.set_payload(file_data)
		encoders.encode_base64(attachment)
		attachment.add_header('content-Disposition', f'attachment; filename="{file_name}"')
		errEmail.attach(attachment)


		# Adding SSL layer of security
		context = ssl.create_default_context()

		# Login and send email
		with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
			smtp.login(email_sender, email_passwd)
			smtp.sendmail(email_sender, email_receiver, errEmail.as_string())



# Creating a main function 
def main():
	retryCount = 0
	cycleCounter = 0
	while retryCount < max_RetryCount:
		try:
			start = time.time()
			# calling the function at run time
			log_cleaned_and_save_output()


			if filecmp.cmp('Reference.txt', 'final_output.txt'):
				print ("Test Passed!")
				retryCount = 0
				cycleCounter += 1
			else:
				print ("Test Failed, retrying...")
				retryCount += 1
				cycleCounter += 1
		# To display any error that occurs that is not related to the logged file
		except Exception as e:
			print (f"An Error Occured: {e}")
			print ("Retrying......")

		# If statment to check if the retry counter limit is reached
		if retryCount == max_RetryCount or cycleCounter == 5:
			print ("Max retry count reached. Exiting")
			finish_Time_Date = datetime.now()
			print ("Test finished at: ", finish_Time_Date)
			emailSender()
			print("Cycle Count: ", cycleCounter)
			break
		print ("Cycle Count: ", cycleCounter)
		end = time.time()
		print(f"Time taken to execute:", (end - start), 's')
# to run only the main blcok when the script is called block
if __name__ == "__main__":
	main()




