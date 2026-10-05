## Context and justification

For every library, it needs to have users, books, librarians, borrowing and returning books. And it can become hard for librarians to manage.
This project is a backend service for a library management system that provides functionality for managing users, books, librarians, borrowing and returning books.

## Analysis and medeling

- **Methods :** UML, BPMN 2.0
- **Tool :** Camunda Modeler, Draw.io

## Products

- **[Class Diagram](./diagrams/images/class-diagram.png)**
- **[Activity Diagram](./diagrams/images/activity-diagram.png)**
- **[Sequence Diagram](./diagrams/images/sequence-diagram.png)**
- **[Use case Diagrams](./diagrams/images/use-case-diagram.png)**
- **[Package Diagram](./diagrams/images/package-diagram.png)**

## Actors

- **Librarian** : A user responsible for managing the library.
- **Administrator** : A user responsible for managing the system.
- **Member** : A member of the library.

## Use cases

- **Add book**
- **Remove book**
- **Update book**
- **Borrow book**
- **Return book**
- **Search book**
- **Add member**
- **Remove member**
- **Update member**
- **Search member**
- **Manage users**
- **View statistics**
- **Generate reports**

## User Stories & Features

### 1. Book Management
* **Add book:** As a librarian/admin, add new books with details like title, author, ISBN, category, and state so staff can log incoming donations or purchases.
* **Remove book:** As a librarian/admin, remove a book from the system when items are lost, damaged, or outdated.
* **Update book:** As a librarian/admin, update book details to ensure catalog information remains accurate.
* **Search book:** As a librarian/admin, search for books by title, author, ISBN, or category to quickly locate reading material.

### 2. Inventory
* **Borrow book:** As a librarian, register a loan of an available book to a library member to keep inventory accurate and track who holds the item.
* **Return book:** As a librarian, register the return of a borrowed book to make it available for other readers.

### 3. Member Management
* **Add member:** As an admin, register a new member with their name, email, password, and role so staff can track loans on their behalf.
* **Remove member:** As an admin, remove a member account so inactive or suspended users lose system access.
* **Update member:** As an admin or librarian, update member profile details to keep contact information current.
* **Search member:** As a librarian/admin, search for members by name or email to quickly manage accounts and check borrowed items.
* **Manage users:** As an admin, manage staff permissions and roles to maintain proper system security and access control.

### 4. Statistics
* **View statistics:** As an administrator, view high-level library statistics (e.g., total books, active loans, popular categories) to monitor system performance.
* **Generate reports:** As an administrator, generate detailed system reports to analyze usage trends and overall inventory health.

## Classes
### User
* **Attributes:**
    - id
    - name
    - email
    - password
    - role
    - create_at
    - last_access
* **Methods**:
    - manage_profile()
    - manage_permissions()
    - viewStatistics()
    - generateReports()

### Book
* **Attributes:**
    - id
    - title
    - author
    - isbn
    - category
    - bookState
* **Methods**:
    - addBook()
    - removeBook()
    - updateBook()
    - borrowBook()
    - returnBook()
    - searchBook()

### Book State
* **Attributes**:
    - id
    - name
* **Methods**:
    - addState()
    - updateState()

### Category
* **Attributes**:
    - id
    - name
* **Methods**:
    - addCategory()
    - removeCategory()
    - updateCategory()

### Role
* **Attributes**:
    - id
    - label
* **Methods**:
    - addRole()
    - removeRole()
    - updateRole()