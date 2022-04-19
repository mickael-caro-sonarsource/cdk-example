sudo yum update -y
sudo yum install -y httpd.x86_64
sudo service httpd start
echo "It works" > index.html
sudo mv index.html /var/www/html/
sudo chkconfig on
