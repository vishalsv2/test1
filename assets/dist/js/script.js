document.addEventListener('DOMContentLoaded', function () {    // Event listener for 'Select All' checkbox
    document.getElementById('select-all').addEventListener('change', function (event) {
        var checkboxes = document.querySelectorAll('.checkbox-primary');
        checkboxes.forEach(function (checkbox) {
            checkbox.checked = event.target.checked;
        });
    });

    // Event listener for 'Bulk Assign' button
    document.getElementById('bulk-assign-button').addEventListener('click', function () {
        var selectedAgent = document.getElementById('bulk-assign-agent').value;
        if (!selectedAgent) {
            Alpine.store('toasts').createToast('Please select an agent to assign tickets to.', 'error');
            return;
        }

        var selectedTickets = Array.from(document.querySelectorAll('.checkbox-primary:checked')).map(function (checkbox) {
            return checkbox.getAttribute('data-ticket-id') || undefined;
        }).filter(id => id);

        if (selectedTickets.length === 0) {
            Alpine.store('toasts').createToast('Please select at least one ticket.', 'error');
            return;
        }
        // Fetch request to the server to assign tickets
        fetch('/v1/api/tickets/assign-tickets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tickets: selectedTickets,
                agent: selectedAgent,
            }),
        })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text || 'Network response was not ok') });
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 200) {
                    Alpine.store('toasts').createToast(data.success, 'success');
                } else {
                    Alpine.store('toasts').createToast(data.error, 'error');
                }
                window.location.reload();
            })
            .catch(error => {
                // Handle errors
                Alpine.store('toasts').createToast('Error assigning tickets: ' + error, 'error');
                console.error('There has been a problem with your fetch operation:', error);
                window.location.reload();
            });
    });
});


    // JavaScript to handle the close ticket process
document.addEventListener('DOMContentLoaded', function () { 
    document.getElementById('closeTicketButton').addEventListener('click', function () {
        var close_ticket = this.getAttribute('ticket-id');
        console.log(close_ticket);
        // Fetch request to the server to assign tickets
        fetch('/v1/api/tickets/close_ticket', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ticket_id: close_ticket,
            }),
        })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text || 'Network response was not ok') });
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 200) {
                    Alpine.store('toasts').createToast(data.success, 'success');
                    if (data.redirect_url) {
                        const sanitizedUrl = encodeURI(data.redirect_url);
                        window.location.href = sanitizedUrl;
                    } else {
                        window.location.reload(); // Reload or fallback if no redirect URL is provided
                    }
                } else {
                    Alpine.store('toasts').createToast(data.error, 'error');
                    window.location.reload();
                }
            })
            .catch(error => {
                // Handle errors
                Alpine.store('toasts').createToast('Error closing tickets: ' + error, 'error');
                console.error('There has been a problem with your fetch operation:', error);
                window.location.reload();    
            });
    });
});

document.addEventListener('DOMContentLoaded', function () { 
    // JavaScript to handle the ticket transfer process
    // JavaScript to handle the ticket transfer process
    document.getElementById('transfer-button').addEventListener('click', function () {
        console.log('Transfer button clicked');
        var assigned_to = document.getElementById('assign-agent').value;
        var transfer_ticket = document.getElementById('ticketId').textContent || document.getElementById('ticketId').innerText;
        console.log(transfer_ticket);
        console.log(assigned_to);
        // Fetch request to the server to assign tickets
        fetch('/v1/api/tickets/transfer_ticket', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ticket_id: transfer_ticket,
                assigned_to: assigned_to,
            }),
        })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text || 'Network response was not ok') });
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 200) {
                    Alpine.store('toasts').createToast(data.success, 'success');
                } else {
                    Alpine.store('toasts').createToast(data.error, 'error');
                }
                window.location.reload();
            })
            .catch(error => {
                // Handle errors
                Alpine.store('toasts').createToast('Error transferring tickets: ' + error, 'error');
                console.error('There has been a problem with your fetch operation:', error);
                window.location.reload();
            });

    });
});

document.addEventListener('DOMContentLoaded', function () { 
    // JavaScript to handle the ticket rejection process
    document.getElementById('reject-button').addEventListener('click', function () {
        var reject_ticket = document.getElementById('pending_ticket').textContent || document.getElementById('pending_ticket').innerText;
        console.log(reject_ticket);
        // Fetch request to the server to assign tickets
        fetch('/v1/api/tickets/transfer_reject', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ticket_id: reject_ticket,
            }),
        })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text || 'Network response was not ok') });
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 200) {
                    Alpine.store('toasts').createToast(data.success, 'success');
                } else {
                    Alpine.store('toasts').createToast(data.error, 'error');
                }
                window.location.reload();
            })
            .catch(error => {
                // Handle errors
                Alpine.store('toasts').createToast('Error rejecting tickets: ' + error, 'error');
                console.error('There has been a problem with your fetch operation:', error);
                window.location.reload();
            });
    });
});

document.addEventListener('DOMContentLoaded', function () {
    // JavaScript to handle the ticket approval process
    // JavaScript to handle the ticket approval process
    document.getElementById('approve-button').addEventListener('click', function () {
        var approve_ticket = document.getElementById('pending_ticket').textContent || document.getElementById('pending_ticket').innerText;
        console.log(approve_ticket);
        // Fetch request to the server to assign tickets
        fetch('/v1/api/tickets/transfer_accept', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ticket_id: approve_ticket,
            }),
        })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text || 'Network response was not ok') });
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 200) {
                    Alpine.store('toasts').createToast(data.success, 'success');
                } else {
                    Alpine.store('toasts').createToast(data.error, 'error');
                }
                window.location.reload();
            })
            .catch(error => {
                // Handle errors
                Alpine.store('toasts').createToast('Error approving tickets: ' + error, 'error');
                console.error('There has been a problem with your fetch operation:', error);
                window.location.reload();
            });

    });
});



document.addEventListener('alpine:init', () => {
    Alpine.store('toasts', {
        counter: 0,
        list: [],
        createToast(message, type = 'info', timer = 2000) {
            const index = this.list.length
            let totalVisible =
                this.list.filter((toast) => {
                    return toast.visible
                }).length + 1
            this.list.push({
                id: this.counter++,
                message,
                type,
                timeOut: timer * totalVisible,
                visible: true,
            })
            setTimeout(() => {
                this.destroyToast(index)
            }, timer * totalVisible)
        },
        destroyToast(index) {
            this.list[index].visible = false
        },
    })
});