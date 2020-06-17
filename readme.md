# Text and images downloader
An Docker application consisting of Flask server and PostgreSQL database. Using REST API create requests for text or images from website. Includes automatic tests.
### Prerequisites
+ Docker [(What is Docker)](https://opensource.com/resources/what-docker)
+All other requirements are automatically installed when creating Docker image.
<br>You can check pip requirements in **requirements.txt** and **pytest.requirements.txt** files.
### Installing
+ Download and install Docker [(Download)](https://docs.docker.com/get-docker/)
+ Navigate in console to downloaded folder
+ Create applications with:
```
docker-compose up -d --build
```
+ If modified database/tables, before rebuilding use:
<br>(this will delete previous requests from database)
```
docker-compose down -v
```
## Usage
Flask application will be listening to requests on __localhost:5000__ or __0.0.0.0:500__.
<br> Available methods, usage and responses are described in **swagger.yaml** [(see swagger.io)](https://editor.swagger.io/)
### Methods
#### POST
##### /get/text/
Create request for text from website. Returns request ID.
##### /get/images/
Create request for images from website. Returns request ID.
#### GET
##### /
Test page to check if server is running.
##### /download/text/\<ID>
Download requested text to **app/Text** folder.
##### /download/images/\<ID>
Download requested text to **app/Images** folder.
## Testing
After building applications, automatic tests will run. You can check results in tests container.
## Info
Flask container might crash after first start (database will be created). It should automatically restart.
<br>Having more than one instance running at the same time might cause problems.
<br>This is an requirement task. It's described in **Task.pdf**
## Built With
[Docker](https://www.docker.com/) - microservice host
<br>[Flask](https://flask.palletsprojects.com/) - local server
<br>[PostgreSQL](https://www.postgresql.org/) - database
<br>[Pytest](https://docs.pytest.org/en/latest/) - automatic tests
<br>[swagger.io](https://swagger.io/) - API documentation
<br>[Postman](https://www.postman.com/) - use for REST API testing

