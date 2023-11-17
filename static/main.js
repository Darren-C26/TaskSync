document.addEventListener('DOMContentLoaded', function () {
    // Fetch the user data from Flask and call displayBoards
    fetch('/user-data')
        .then(response => response.json())
        .then(data => {
            displayBoards(data.boards_data);
            displayAccountInfo(data.user_data);
        });
});

// Function to display user account information in the modal
function displayAccountInfo(user) {
    const accountInfoBody = document.getElementById('accountInfoBody');

    // Example: Display user ID and username
    const userInfoHTML = `<p>User ID: ${user.id}</p><p>Username: ${user.username}</p>`;

    accountInfoBody.innerHTML = userInfoHTML;
}

// Function to update the user's profile picture
function updateProfilePicture() {
    // Get the file input and selected file
    const fileInput = document.getElementById('profile-picture-input');
    const file = fileInput.files[0];

    if (file) {
        // Create a FormData object and append the file to it
        const formData = new FormData();
        formData.append('file', file);

        // Send a POST request to the server to update the profile picture
        fetch('/update_profile_picture', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': '{{ csrf_token() }}',  // Replace with your CSRF token
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                // If the update is successful, update the profile picture on the page
                document.getElementById('profile-picture').src = `/profile_pictures/${file.name}`;
                alert(data.message);
            } else {
                alert('Profile picture update failed');
            }
        });
    } else {
        alert('Please select a file');
    }
}

function register() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
    })
    .then(response => {
        if (response.ok) {
            alert('Registration successful!');
        } else {
            alert('Registration failed. Please try again.');
        }
    });
}

function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
    })
    .then(response => response.json())
    .then(data => {
        if ('message' in data) {
            // Redirect to the dashboard
            window.location.href = data.redirect;

        } else {
            // Handle error messages, e.g., display an alert
            alert(data.error);
        }
    });
}

function logout() {
    fetch('/logout')
    .then(response => response.json())
    .then(data => {
        if ('message' in data) {
            // Redirect to the dashboard
            window.location.href = data.redirect;
        } else {
            // Handle error messages, e.g., display an alert
            alert(data.error);
        }
    });
}

// Function to create a new board
function createBoard() {
    const boardName = document.getElementById('boardName').value;
    fetch('/create_board', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: boardName }),
    })
    .then(response => {
        if (response.ok) {
            alert('Board created successfully!');
            // Refresh the board list after creating a new board
            window.location.href = '/dashboard';
        } else {
            alert('Board creation failed. Please try again.');
        }
    });
}

// Function to display user information and profile picture
function displayUser(user) {
    document.getElementById('username').innerText = user.username;
    document.getElementById('profile-picture').src = user.profile_picture;
}

// Function to display boards and tasks dynamically
function displayBoards(boards) {
    const boardList = document.getElementById('boardList');
    boardList.innerHTML = '';
    boards.forEach(board => {
        const boardItem = document.createElement('div');
        boardItem.classList.add('board-container');
        displayColumns(board, boardItem);

        // Create a delete button for each board
        const deleteButton = document.createElement('button');
        deleteButton.textContent = 'Delete Board';
        deleteButton.classList.add('btn', 'btn-danger', 'btn-sm');
        deleteButton.addEventListener('click', () => deleteBoard(board.id));

        // Append the delete button to the board container
        boardItem.appendChild(deleteButton);

        // Append the board container to the board list
        boardList.appendChild(boardItem);
    });
}

// Add this function to your main.js file
function deleteBoard(boardId) {
    const confirmation = confirm("Are you sure you want to delete this board?");

    if (confirmation) {
        fetch(`/delete_board/${boardId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => {
            if (response.ok) {
                alert('Board deleted successfully!');
                // Refresh the page or update the board list
                window.location.reload();
            } else {
                alert('Board deletion failed. Please try again.');
            }
        });
    }
}

// Function to display columns for a selected board
function displayColumns(board, boardItem) {
    // Set the board title
    const boardTitle = document.createElement('h2');
    boardTitle.textContent = board.name;
    boardItem.appendChild(boardTitle);

    const columnsDiv = document.createElement('div');
    columnsDiv.id = board.id;
    columnsDiv.classList.add('columns-container');
    boardItem.appendChild(columnsDiv);

    // Display columns
    board.columns.forEach(column => {
        const columnDiv = document.createElement('div');
        columnDiv.id = `board${board.id}-column${column.id}`;
        columnDiv.classList.add('column');

        const columnTitle = document.createElement('h3');
        columnTitle.textContent = column.name;

        const tasksList = document.createElement('div');
        tasksList.id = `board${board.id}-tasks${column.id}`;

        // Display tasks in the column
        column.tasks.forEach(task => {
            const taskItem = document.createElement('div');
            taskItem.classList.add('task');
            taskItem.draggable = true;  // Make the task draggable
            taskItem.id = `task${task.id}`;  // Assign a unique id to the task element
            taskItem.innerHTML = `
                <div class="task-content" contenteditable="true">${task.content}</div>
                <div class="task-buttons">
                    <button class="btn btn-sm move-button">Move</button>
                    <button class="btn btn-info btn-sm update-button">Update</button>
                    <button class="btn btn-danger btn-sm delete-button">Delete</button>
                </div>
            `;

            // Add event listeners for move and delete buttons
            const moveButton = taskItem.querySelector('.move-button');
            const updateButton = taskItem.querySelector('.update-button');
            const deleteButton = taskItem.querySelector('.delete-button');

            moveButton.addEventListener('click', () => moveTask(task.id, column.id));
            updateButton.addEventListener('click', (e) => {
                e.stopPropagation();
                updateTask(task.id);
            });
            deleteButton.addEventListener('click', (e) => {
                e.stopPropagation(); // Stop the event from propagating to the parent elements
                deleteTask(task.id);
            });

            // Add event listener for drag start
            taskItem.addEventListener('dragstart', (e) => handleDragStart(e, task.id));

            // Add event listener for drag over and drop
            tasksList.addEventListener('dragover', (e) => handleDragOver(e));
            tasksList.addEventListener('drop', (e) => handleDrop(e, board.id));

            tasksList.appendChild(taskItem);
        });

        const taskInput = document.createElement('textarea');
        taskInput.placeholder = 'Add Task';
        taskInput.style.width = '97%';
        taskInput.style.margin = '5px';
        taskInput.style.padding = '5px';
        taskInput.style.resize = 'none';

        const addTaskButton = document.createElement('button');
        addTaskButton.textContent = 'Add Task';
        addTaskButton.addEventListener('click', () => addTask(board.id, column.id, taskInput));
        addTaskButton.style.margin = '5px';
        addTaskButton.classList.add('btn');
        addTaskButton.classList.add('btn-sm');
        columnDiv.appendChild(columnTitle);
        columnDiv.appendChild(tasksList);
        columnDiv.appendChild(taskInput);
        columnDiv.appendChild(addTaskButton);

        columnsDiv.appendChild(columnDiv);
    });

    // Make columns droppable
    columnsDiv.addEventListener('dragover', (e) => handleDragOver(e));
    columnsDiv.addEventListener('drop', (e) => handleDrop(e, board.id));
}

// Function to add a new task to a column
function addTask(boardId, columnId, taskInput) {
    const task = taskInput.value;

    fetch(`/add_task/${boardId}/${columnId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content: task }),
    })
    .then(response => {
        if (response.ok) {
            alert('Task added successfully!');
            // Refresh the columns after adding a task
            window.location.href = '/dashboard';
        } else {
            alert('Task addition failed. Please try again.');
        }
    });
}

// Function to handle drag start for tasks
function handleDragStart(e, taskId) {
    e.dataTransfer.setData('text/plain', taskId);
}

// Function to handle drag over for columns
function handleDragOver(e) {
    e.preventDefault();
}

// Function to handle drop for tasks
function handleDrop(e, boardId) {
    e.preventDefault();
    const taskId = e.dataTransfer.getData('text/plain');
    const columnId = e.target.id.split('column')[1];

    fetch(`/move_task/${taskId}/${columnId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ boardId }),
    })
    .then(response => {
        if (response.ok) {
            alert('Task moved successfully!');
            // Refresh the columns after moving a task
            window.location.href = '/dashboard';
        } else {
            alert('Task movement failed. Please try again.');
        }
    });
}

// Function to move a task to a different column
function moveTask(taskId, targetColumnId) {
    fetch(`/move_task/${taskId}/${targetColumnId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
    })
    .then(response => {
        if (response.ok) {
            alert('Task moved successfully!');
            // Refresh the columns after moving a task
            window.location.href = '/dashboard';
        } else {
            alert('Task movement failed. Please try again.');
        }
    });
}

// Function to delete a task
function deleteTask(taskId) {
    fetch(`/delete_task/${taskId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        if (response.ok) {
            alert('Task deleted successfully!');
            // Refresh the columns after deleting a task
            window.location.href = '/dashboard';
        } else {
            alert('Task deletion failed. Please try again.');
        }
    });
}

// Function to update a task
function updateTask(taskId) {
    const updatedContent = document.getElementById(`task${taskId}`).querySelector('.task-content').textContent;
    fetch(`/update_task/${taskId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content: updatedContent }),
    })
    .then(response => {
        if (response.ok) {
            alert('Task updated successfully!');
            // Refresh the columns after updating a task
            window.location.href = '/dashboard';
        } else {
            alert('Task update failed. Please try again.');
        }
    });
}