Here's a revised version of the README file that includes the steps you provided, ensuring all the details match your project steps:

---

# MongoDB + Python Flask Web Framework + REST API + GKE

This project involves creating a MongoDB database using persistent volume on GKE, deploying a Python Flask web application and a Node.js server to fetch records from MongoDB, and exposing these applications using Ingress with Nginx. The project is divided into several steps, detailed below.

## Table of Contents

- [MongoDB Deployment on GKE](#mongodb-deployment-on-gke)
- [StudentServer Setup](#studentserver-setup)
- [Flask Application Setup](#flask-application-setup)
- [ConfigMap Creation](#configmap-creation)
- [Ingress Setup](#ingress-setup)
- [Testing the Applications](#testing-the-applications)

## MongoDB Deployment on GKE

### Step 1: Create MongoDB Using Persistent Volume on GKE and Insert Records

1. **Create a GKE Cluster:**
    ```bash
    gcloud container clusters create kubia --num-nodes=1 --machine-type=e2-micro --region=us-west1
    ```
    Wait for the cluster creation to finish.

2. **Create Persistent Volume:**
    ```bash
    gcloud compute disks create --size=10GiB --zone=us-west1-a mongodb
    ```

3. **Deploy MongoDB:**
    Apply the `mongodb-deployment.yaml` configuration:
    ```yaml
    apiVersion: v1
    kind: PersistentVolume
    metadata:
      name: mongodb-pv
    spec:
      capacity:
        storage: 10Gi
      accessModes:
        - ReadWriteOnce
      gcePersistentDisk:
        pdName: mongodb
        fsType: ext4
    ---
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      name: mongodb-pvc
    spec:
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 10Gi
    ---
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: mongodb-deployment
    spec:
      selector:
        matchLabels:
          app: mongodb
      strategy:
        type: Recreate
      template:
        metadata:
          labels:
            app: mongodb
        spec:
          containers:
          - image: mongo
            name: mongo
            ports:
            - containerPort: 27017
            volumeMounts:
            - name: mongodb-data
              mountPath: /data/db
          volumes:
          - name: mongodb-data
            persistentVolumeClaim:
              claimName: mongodb-pvc
    ```
    ```bash
    kubectl apply -f mongodb-deployment.yaml
    ```

4. **Check Deployment Status:**
    ```bash
    kubectl get pods
    ```
    Ensure the pod status is `Running`.

5. **Create MongoDB Service:**
    Apply the `mongodb-service.yaml` configuration:
    ```yaml
    apiVersion: v1
    kind: Service
    metadata:
      name: mongodb-service
    spec:
      type: LoadBalancer
      ports:
      - port: 27017
        targetPort: 27017
      selector:
        app: mongodb
    ```
    ```bash
    kubectl apply -f mongodb-service.yaml
    ```

6. **Verify Service Status:**
    ```bash
    kubectl get svc
    ```
    Wait for the `EXTERNAL-IP` to be assigned.

7. **Test MongoDB Connection:**
    ```bash
    kubectl exec -it mongodb-deployment-replace-with-your-pod-name -- bash
    ```

8. **Insert Records into MongoDB:**
    Use the following Node.js script to insert data into MongoDB:
    ```javascript
    const { MongoClient } = require('mongodb');

    async function run() {
      const url = "mongodb://<EXTERNAL-IP>/studentdb"; // Use the correct IP and port
      const client = new MongoClient(url, { useNewUrlParser: true, useUnifiedTopology: true });

      try {
        await client.connect();
        const db = client.db("studentdb");
        const collection = db.collection("students");

        const docs = [
          { student_id: 11111, student_name: "Bruce Lee", grade: 84 },
          { student_id: 22222, student_name: "Jackie Chan", grade: 93 },
          { student_id: 33333, student_name: "Jet Li", grade: 88 }
        ];

        const insertResult = await collection.insertMany(docs);
        console.log(`${insertResult.insertedCount} documents were inserted`);

        const result = await collection.findOne({ student_id: 11111 });
        console.log(result);
      } finally {
        await client.close();
      }
    }
    run().catch(console.dir);
    ```

## StudentServer Setup

### Step 2: Modify StudentServer to Fetch Records from MongoDB and Deploy to GKE

1. **Create `studentServer.js`:**
    ```javascript
    const http = require('http');
    const url = require('url');
    const { MongoClient } = require('mongodb');
    const { MONGO_URL, MONGO_DATABASE } = process.env;

    const uri = `mongodb://${MONGO_URL}/${MONGO_DATABASE}`;
    console.log(uri);

    const server = http.createServer(async (req, res) => {
      try {
        const parsedUrl = url.parse(req.url, true);
        const student_id = parseInt(parsedUrl.query.student_id);

        if (/^\/api\/score/.test(req.url)) {
          const client = new MongoClient(uri);
          await client.connect();
          const db = client.db("studentdb");

          const student = await db.collection("students").findOne({ "student_id": student_id });
          await client.close();

          if (student) {
            const response = {
              student_id: student.student_id,
              student_name: student.student_name,
              student_score: student.grade
            };

            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(response) + '\n');
          } else {
            res.writeHead(404);
            res.end("Student Not Found\n");
          }
        } else {
          res.writeHead(404);
          res.end("Wrong URL, please try again\n");
        }
      } catch (err) {
        console.error(err);
        res.writeHead(500);
        res.end("Internal Server Error\n");
      }
    });

    server.listen(8080, () => {
      console.log('Server is listening on port 8080');
    });
    ```

2. **Create `Dockerfile`:**
    ```Dockerfile
    FROM node:14
    WORKDIR /app
    COPY package*.json ./
    RUN npm install
    COPY studentServer.js ./
    EXPOSE 8080
    ENTRYPOINT ["node", "studentServer.js"]
    ```

3. **Create `package.json`:**
    ```json
    {
      "name": "studentserver",
      "version": "1.0.0",
      "description": "Student Server",
      "main": "studentServer.js",
      "scripts": {
        "start": "node studentServer.js"
      },
      "dependencies": {
        "mongodb": "^4.0.0",
        "http": "0.0.1-security"
      }
    }
    ```

4. **Build Docker Image:**
    ```bash
    docker build -t yourdockerhubID/studentserver .
    ```

5. **Push Docker Image to Docker Hub:**
    ```bash
    docker push yourdockerhubID/studentserver
    ```

## Flask Application Setup

### Step 3: Create the Flask Application

1. **Create `bookshelf.py`:**
    ```python
    from flask import Flask, request, jsonify
    from flask_pymongo import PyMongo
    from bson.objectid import ObjectId
    import socket
    import os

    app = Flask(__name__)
    app.config["MONGO_URI"] = "mongodb://" + os.getenv("MONGO_URL") + "/" + os.getenv("MONGO_DATABASE")
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    mongo = PyMongo(app)
    db = mongo.db

    @app.route("/")
    def index():
        hostname = socket.gethostname()
        return jsonify(message="Welcome to bookshelf app! I am running inside {} pod!".format(hostname))

    @app.route("/books")
    def get_all_books():
        books = db.bookshelf.find()
        data = []
        for book in books:
            data.append({
                "id": str(book["_id"]),
                "Book Name": book["book_name"],
                "Book Author": book["book_author"],
                "ISBN": book["ISBN"]
            })
        return jsonify(data)

    @app.route("/book", methods=["POST"])
    def add_book():
        book = request.get_json(force=True)
        db.bookshelf.insert_one({
            "book_name": book["book_name"],
            "book_author": book["book_author"],
            "ISBN": book["isbn"]
        })
        return jsonify(message="Book saved successfully!")

    @app.route("/book/<id>", methods=["PUT"])
    def update_book(id):
        data = request.get_json(force=True)
        response = db.bookshelf.update_one({"_id": ObjectId(id)}, {"$set": {
            "book_name": data['book_name'],
            "book_author": data["book_author"],
            "ISBN": data["isbn"]
        }})
        message =

 "Book Updated Successfully!" if response else "Nothing to Update!"
        return jsonify(message=message)

    @app.route("/book/<id>", methods=["DELETE"])
    def delete_book(id):
        response = db.bookshelf.delete_one({"_id": ObjectId(id)})
        message = "Book Deleted Successfully!" if response else "Book Not Available!"
        return jsonify(message=message)

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000, debug=True)
    ```

2. **Create `requirements.txt`:**
    ```
    Flask==2.1.1
    Flask-PyMongo==2.3.0
    pymongo==3.12.0
    dnspython==2.1.0
    ```

3. **Create `Dockerfile`:**
    ```Dockerfile
    FROM python:3.8-slim
    WORKDIR /app
    COPY requirements.txt requirements.txt
    RUN pip install -r requirements.txt
    COPY . .
    ENTRYPOINT ["python"]
    CMD ["bookshelf.py"]
    ```

4. **Build Docker Image:**
    ```bash
    docker build -t yourdockerhubID/bookshelf .
    ```

5. **Push Docker Image to Docker Hub:**
    ```bash
    docker push yourdockerhubID/bookshelf
    ```

## ConfigMap Creation

### Step 4: Create a ConfigMap for Environment Variables

1. **Create `app-config.yaml`:**
    ```yaml
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: app-config
    data:
      MONGO_URL: "mongodb-service:27017"
      MONGO_DATABASE: "studentdb"
    ```
    ```bash
    kubectl apply -f app-config.yaml
    ```

## Ingress Setup

### Step 5: Create and Configure the Ingress

1. **Create `studentserver-deployment.yaml`:**
    ```yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: studentserver
    spec:
      selector:
        matchLabels:
          app: studentserver
      template:
        metadata:
          labels:
            app: studentserver
        spec:
          containers:
          - name: studentserver
            image: yourdockerhubID/studentserver
            ports:
            - containerPort: 8080
            envFrom:
            - configMapRef:
                name: app-config
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: studentserver-service
    spec:
      selector:
        app: studentserver
      ports:
        - protocol: TCP
          port: 80
          targetPort: 8080
    ```
    ```bash
    kubectl apply -f studentserver-deployment.yaml
    ```

2. **Create `bookshelf-deployment.yaml`:**
    ```yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: bookshelf
    spec:
      selector:
        matchLabels:
          app: bookshelf
      template:
        metadata:
          labels:
            app: bookshelf
        spec:
          containers:
          - name: bookshelf
            image: yourdockerhubID/bookshelf
            ports:
            - containerPort: 5000
            envFrom:
            - configMapRef:
                name: app-config
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: bookshelf-service
    spec:
      selector:
        app: bookshelf
      ports:
        - protocol: TCP
          port: 80
          targetPort: 5000
    ```
    ```bash
    kubectl apply -f bookshelf-deployment.yaml
    ```

3. **Create `ingress.yaml`:**
    ```yaml
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    metadata:
      name: ingress
      annotations:
        nginx.ingress.kubernetes.io/rewrite-target: /
    spec:
      rules:
      - http:
          paths:
          - path: /student
            pathType: Prefix
            backend:
              service:
                name: studentserver-service
                port:
                  number: 80
          - path: /books
            pathType: Prefix
            backend:
              service:
                name: bookshelf-service
                port:
                  number: 80
    ```
    ```bash
    kubectl apply -f ingress.yaml
    ```

## Testing the Applications

### Step 6: Test the Applications

1. **Verify the Ingress IP:**
    ```bash
    kubectl get ingress
    ```

2. **Test StudentServer:**
    ```
    curl http://<INGRESS-IP>/student/api/score?student_id=11111
    ```

3. **Test Flask Application:**
    ```
    curl http://<INGRESS-IP>/books
    ```

4. **Add a New Book:**
    ```bash
    curl -X POST http://<INGRESS-IP>/book -H "Content-Type: application/json" -d '{"book_name": "New Book", "book_author": "Author Name", "isbn": "123456"}'
    ```

---

This comprehensive README includes all the necessary steps for deploying and testing the applications on GKE, ensuring that everything is covered from the initial setup to the final verification.

## Testing and Validation

### Testing Strategy
- **Unit Tests:** Verify individual components.
- **Integration Tests:** Ensure components work together seamlessly.
- **End-to-End Tests:** Validate the entire application workflow.

### Types of Tests
- **Functional Tests:** Test API endpoints and their functionality.
- **Performance Tests:** Measure application performance and scalability.

### Tools and Frameworks
- **Postman:** For API testing.
- **Pytest:** For automated testing of the Flask application.

### Example Test Cases
- **Retrieve Student Record:** Ensure correct data is fetched for a given student ID.
- **Insert Bookstore Record:** Verify that new records can be added to the bookstore.
- **Error Handling:** Check how the application handles invalid inputs and errors.

## Future Enhancements

### Potential Improvements
- **User Interface:** Develop a frontend using React or Angular.
- **Authentication:** Implement user authentication and authorization.

### Performance Optimizations
- **Database Queries:** Optimize MongoDB queries for better performance.
- **Caching:** Use caching mechanisms to improve response times.

### Security Enhancements
- **SSL/TLS:** Implement secure communication channels.
- **Environment Variables:** Securely manage sensitive data using environment variables.

### Additional Functionalities
- **Analytics and Reporting:** Add features for detailed analytics and reporting.
- **Payment Integration:** Integrate with payment gateways for transaction management.

## Conclusion

### Summary of Accomplishments
- Successfully integrated MongoDB with a Python Flask application.
- Deployed the application on GKE for scalability and reliability.

### Key Learnings
- Gained experience with Kubernetes and container orchestration.
- Learned how to integrate multiple technologies to build a robust application.

### Impact and Benefits
- Improved data management for student and bookstore records.
- Achieved a scalable and robust web application.

### Future Outlook
- Plan to expand the application with more features and enhancements.

## References

### Resources
- **MongoDB Documentation:** [MongoDB Docs](https://docs.mongodb.com/)
- **Flask Documentation:** [Flask Docs](https://flask.palletsprojects.com/)
- **Kubernetes Documentation:** [Kubernetes Docs](https://kubernetes.io/docs/)

### Guides and Tutorials
- **Google Cloud Tutorials:** [GCP Tutorials](https://cloud.google.com/docs/tutorials)
- **REST API Best Practices:** [REST API Guide](https://restfulapi.net/)

## Appendix
- [Detialed Slides Presentation](https://www.canva.com/design/DAGMgHLIpZs/lDBwSSEc3MBd95kjDTzODg/edit?utm_content=DAGMgHLIpZs&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)
- [PDF documentation of every step]()
