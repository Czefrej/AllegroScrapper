cd lambda
rm lambda.zip
7z a lambda.zip ../ -r -x!*.zip
aws lambda update-function-code --function-name CategoryScrapper --zip-file fileb://lambda.zip --cli-connect-timeout 6000
read -n 1 -s -r -p "Press any key to continue"