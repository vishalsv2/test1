window.onload = function() {
    // Read the toast message from the data attribute of the hidden div
    const toastDataElement = document.getElementById('toast-data');
    const toastMessage = JSON.parse(toastDataElement.getAttribute('data-toast') || '{}');

    if (toastMessage && toastMessage.status && toastMessage.message) {
        let toastHTML = `
            <div class="toast bg-${toastMessage.status}" role="alert" aria-live="assertive" aria-atomic="true" data-delay="5000">
                <div class="toast-header">
                    <strong class="mr-auto">Notification</strong>
                    <button type="button" class="ml-2 mb-1 close" data-dismiss="toast" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="toast-body">
                    ${toastMessage.message}
                </div>
            </div>`;

        // Append the toast HTML
        document.getElementById('toast-container').innerHTML = toastHTML;
        // Show the toast
        $('.toast').toast('show');
    }
};
