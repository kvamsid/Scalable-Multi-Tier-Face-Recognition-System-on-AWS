# Scalable-Multi-Tier-Face-Recognition-System-on-AWS

# Scalable Face Recognition System

## Overview
This project is a cloud-native application built on AWS to deliver efficient and scalable face recognition. Designed to handle high volumes of concurrent requests, it employs a multi-tier architecture that dynamically adjusts resource allocation. The system uses EC2 instances for computation, S3 for persistent storage, and SQS for inter-service communication, while leveraging a PyTorch-based deep learning model for accurate face detection and identification.

![System Architecture](assets/scalable.png)

## Key Advantages
- **Layered Architecture**: The application is divided into three independent tiers—web, application, and data—to promote modularity and facilitate seamless scalability.
- **Dynamic Auto-Scaling**: A custom scaling algorithm automatically provisions up to 20 EC2 instances to meet fluctuating demand.
- **Advanced Deep Learning**: Utilizes a robust PyTorch model to ensure high-precision face recognition.
- **Reliable Data Management**: All input images and processing results are stored securely in S3 buckets.
- **User-Friendly Web Interface**: A Flask-based service in `web_tier.py` processes incoming HTTP POST requests and manages backend communication.

## System Breakdown

### Web Tier
- **Role**: Serves as the primary interface for client interactions.
- **Functionality**: 
  - Receives HTTP POST requests containing image data.
  - Initiates communication with the SQS queues to dispatch tasks to the application tier.
  - Oversees the auto-scaling mechanism based on the current load.
- **Implementation**: Managed by the `web_tier.py` script, located in the `web-tier/` directory.

### Application Tier
- **Role**: Handles the core processing tasks.
- **Functionality**: 
  - Processes incoming requests by invoking the PyTorch-based face recognition model.
  - Sends processed results back to the web tier.
- **Deployment**: Runs on EC2 instances using a custom AMI.
- **Implementation**: Comprises two key scripts:
  - `face_recognition.py`: Contains the PyTorch model for performing face recognition, located in the `app-tier/` directory.
  - `app_tier.py`: Manages request processing and coordination on the application layer, also located in the `app-tier/` directory.

### Data Tier
- **Role**: Provides robust and scalable storage.
- **Functionality**: 
  - Stores original images and processed classification results.
- **Implementation**: Utilizes AWS S3 buckets for durable and scalable data storage.

## File Structure
- **`web_tier.py`**: Found in `web-tier/`, this script is the entry point for client requests, managing both the SQS interactions and auto-scaling processes.
- **`face_recognition.py`**: Located in `app-tier/`, this module contains the PyTorch model used for face recognition.
- **`app_tier.py`**: Also in `app-tier/`, this script is responsible for the orchestration of tasks within the application layer.

---

This system architecture ensures efficient face recognition processing at scale while maintaining robust, modular components that can be independently managed and scaled based on operational needs.
