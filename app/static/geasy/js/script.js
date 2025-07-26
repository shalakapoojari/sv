// Form validation and interactions
document.addEventListener("DOMContentLoaded", () => {
  // Add loading states to forms
  const forms = document.querySelectorAll("form")
  forms.forEach((form) => {
    form.addEventListener("submit", (e) => {
      const submitBtn = form.querySelector('button[type="submit"]')
      if (submitBtn) {
        submitBtn.classList.add("loading")
        submitBtn.textContent = "Processing..."
      }
    })
  })

  // Add smooth animations to table rows
  const tableRows = document.querySelectorAll("tbody tr")
  tableRows.forEach((row, index) => {
    row.style.animationDelay = `${index * 0.1}s`
    row.classList.add("fade-in")
  })

  // Form validation
  const inputs = document.querySelectorAll(".form-input, .form-select")
  inputs.forEach((input) => {
    input.addEventListener("blur", validateField)
    input.addEventListener("input", clearError)
  })
})

function validateField(e) {
  const field = e.target
  const value = field.value.trim()

  // Remove existing error styling
  field.classList.remove("error")

  // Basic validation
  if (field.hasAttribute("required") && !value) {
    showFieldError(field, "This field is required")
    return false
  }

  // Email validation
  if (field.type === "email" && value) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(value)) {
      showFieldError(field, "Please enter a valid email address")
      return false
    }
  }

  // Phone validation
  if (field.name === "mobile" && value) {
    const phoneRegex = /^[+]?[1-9][\d]{0,15}$/
    if (!phoneRegex.test(value.replace(/[\s\-$$$$]/g, ""))) {
      showFieldError(field, "Please enter a valid phone number")
      return false
    }
  }

  return true
}

function showFieldError(field, message) {
  field.style.borderColor = "var(--danger)"

  // Remove existing error message
  const existingError = field.parentNode.querySelector(".error-message")
  if (existingError) {
    existingError.remove()
  }

  // Add error message
  const errorDiv = document.createElement("div")
  errorDiv.className = "error-message"
  errorDiv.style.color = "var(--danger)"
  errorDiv.style.fontSize = "0.75rem"
  errorDiv.style.marginTop = "0.25rem"
  errorDiv.textContent = message
  field.parentNode.appendChild(errorDiv)
}

function clearError(e) {
  const field = e.target
  field.style.borderColor = "var(--border-gray)"

  const errorMessage = field.parentNode.querySelector(".error-message")
  if (errorMessage) {
    errorMessage.remove()
  }
}

function confirmDelete(userId) {
  if (confirm("Are you sure you want to delete this employee? This action cannot be undone.")) {
    // Add loading state
    const deleteBtn = event.target
    deleteBtn.textContent = "Deleting..."
    deleteBtn.disabled = true

    // Simulate API call
    setTimeout(() => {
      showNotification("Employee deleted successfully", "success")
      // Remove the row or redirect
      deleteBtn.closest("tr").style.opacity = "0.5"
    }, 1000)
  }
}

function showNotification(message, type = "success") {
  // Remove existing notifications
  const existingNotifications = document.querySelectorAll(".notification")
  existingNotifications.forEach((notification) => notification.remove())

  // Create new notification
  const notification = document.createElement("div")
  notification.className = `notification ${type}`
  notification.textContent = message
  document.body.appendChild(notification)

  // Show notification
  setTimeout(() => {
    notification.classList.add("show")
  }, 100)

  // Hide notification after 3 seconds
  setTimeout(() => {
    notification.classList.remove("show")
    setTimeout(() => {
      notification.remove()
    }, 300)
  }, 3000)
}

// Search functionality
function handleSearch(event) {
  event.preventDefault()
  const searchTerm = event.target.search.value.toLowerCase()
  const tableRows = document.querySelectorAll("tbody tr")

  tableRows.forEach((row) => {
    const text = row.textContent.toLowerCase()
    if (text.includes(searchTerm)) {
      row.style.display = ""
    } else {
      row.style.display = "none"
    }
  })

  showNotification(`Search completed for: ${searchTerm}`, "success")
}

// Auto-generate login ID from name
function generateLoginId() {
  const nameField = document.querySelector('input[name="name"]')
  const loginIdField = document.querySelector('input[name="login_id"]')

  if (nameField && loginIdField && !loginIdField.value) {
    nameField.addEventListener("blur", function () {
      const name = this.value.trim()
      if (name) {
        const loginId = name
          .toLowerCase()
          .replace(/\s+/g, ".")
          .replace(/[^a-z0-9.]/g, "")
        loginIdField.value = loginId
      }
    })
  }
}

// Initialize auto-generation on register page
if (window.location.pathname.includes("register")) {
  generateLoginId()
}

// Password strength indicator
function addPasswordStrengthIndicator() {
  const passwordField = document.querySelector('input[name="password"]')
  if (passwordField) {
    passwordField.addEventListener("input", function () {
      const password = this.value
      const strength = calculatePasswordStrength(password)
      showPasswordStrength(this, strength)
    })
  }
}

function calculatePasswordStrength(password) {
  let score = 0
  if (password.length >= 8) score++
  if (/[a-z]/.test(password)) score++
  if (/[A-Z]/.test(password)) score++
  if (/[0-9]/.test(password)) score++
  if (/[^A-Za-z0-9]/.test(password)) score++

  return score
}



//does automatic search of entered login id and name in employees.html
document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("employee-search");
    const tableBody = document.getElementById("employee-table-body");

    searchInput.addEventListener("input", function () {
        const searchValue = searchInput.value;

        fetch("/geasy/manage/employees/data", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ search: searchValue })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            let rows = "";

            if (!Array.isArray(data) || data.length === 0) {
                rows = `<tr><td colspan="10" class="text-center">No employees found.</td></tr>`;
            } else {
                data.forEach(emp => {
                    rows += `
                        <tr>
                            <td>${emp.login_id}</td>
                            <td>${emp.name}</td>
                            <td>${emp.password}</td>
                            <td>${emp.mobile}</td>
                            <td>${emp.mobile2}</td>
                            <td>
                                <span class="status-badge ${emp.status === 'active' ? 'status-active' : 'status-inactive'}">
                                    ${emp.status}
                                </span>
                            </td>
                            <td>—</td>
                            <td>—</td>
                            <td>
                                <div class="actions-group">
                                    <a href="/manage/employees/edit/${emp.id}" class="btn btn-secondary btn-sm">Edit</a>
                                    <a href="/manage/employees/delete/${emp.id}" class="btn btn-danger btn-sm"
                                       onclick="return confirm('Are you sure you want to delete this employee?')">Delete</a>
                                    <a href="#" class="btn btn-warning btn-sm">Recharge</a>
                                </div>
                            </td>
                        </tr>
                    `;
                });
            }

            tableBody.innerHTML = rows;
        })
        .catch(error => {
            console.error("Fetch error:", error);
            tableBody.innerHTML = `<tr><td colspan="10" class="text-center text-danger">Error loading employees</td></tr>`;
        });
    });
});

function closeEditOverlay() {
    document.getElementById('edit-overlay').style.display = 'none';
    document.getElementById('edit-content').innerHTML = '<button onclick="closeEditOverlay()" style="position: absolute; top: 10px; right: 10px;">✖</button>';
}

document.addEventListener('DOMContentLoaded', () => {
    const editButtons = document.querySelectorAll('.edit-btn');
    editButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const loginId = btn.getAttribute('data-login-id');
            fetch(`/manage/employee/edit/${loginId}`)
                .then(res => {
                    if (!res.ok) throw new Error("Failed to load edit page");
                    return res.text();
                })
                .then(html => {
                    document.getElementById('edit-overlay').style.display = 'block';
                    document.getElementById('edit-content').innerHTML += html;
                })
                .catch(err => alert(err.message));
        });
    });
});
