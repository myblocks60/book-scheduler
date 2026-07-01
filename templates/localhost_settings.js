(function() {
    // Only run on localhost / 127.0.0.1
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    if (!isLocalhost) return;

    // Helper functions for cookies
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    function setCookie(name, value, days = 365) {
        const d = new Date();
        d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = `expires=${d.toUTCString()}`;
        document.cookie = `${name}=${value};${expires};path=/`;
    }

    // Inject styles for the popup and settings icon
    const styles = `
        /* Settings Gear Icon */
        .lh-settings-btn {
            background: none;
            border: none;
            color: #666;
            cursor: pointer;
            padding: 8px;
            font-size: 1.4rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: all 0.3s ease;
            margin-left: 10px;
            width: auto;
            vertical-align: middle;
        }
        .lh-settings-btn:hover {
            background-color: rgba(0, 123, 255, 0.1);
            color: #007bff;
            transform: rotate(45deg);
        }
        
        /* Popup Overlay */
        .lh-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(5px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
        }
        .lh-overlay.active {
            opacity: 1;
            pointer-events: auto;
        }
        
        /* Popup Box */
        .lh-popup {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
            width: 90%;
            max-width: 400px;
            transform: scale(0.9);
            transition: transform 0.3s ease;
        }
        .lh-overlay.active .lh-popup {
            transform: scale(1);
        }
        
        .lh-popup h3 {
            margin-top: 0;
            margin-bottom: 15px;
            color: #333;
            font-size: 1.3em;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .lh-popup .form-group {
            margin-bottom: 15px;
            text-align: left;
        }
        
        .lh-popup label {
            display: block;
            font-weight: 600;
            margin-bottom: 6px;
            color: #555;
            font-size: 0.9em;
        }
        
        .lh-popup input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 6px;
            font-size: 14px;
            box-sizing: border-box;
        }
        
        .lh-popup .btn-group {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        
        .lh-popup button {
            padding: 12px 20px;
            font-size: 14px;
            border-radius: 6px;
            cursor: pointer;
            border: none;
            font-weight: bold;
            flex: 1;
            margin: 0;
        }
        
        .lh-popup .btn-submit {
            background-color: #007bff;
            color: white;
        }
        .lh-popup .btn-submit:hover {
            background-color: #0056b3;
        }
        
        .lh-popup .btn-cancel {
            background-color: #e9ecef;
            color: #495057;
        }
        .lh-popup .btn-cancel:hover {
            background-color: #dee2e6;
        }
    `;

    const styleSheet = document.createElement("style");
    styleSheet.innerText = styles;
    document.head.appendChild(styleSheet);

    // Create the Popup Overlay and Form HTML
    const overlay = document.createElement('div');
    overlay.className = 'lh-overlay';
    overlay.id = 'lhSettingsOverlay';
    overlay.innerHTML = `
        <div class="lh-popup">
            <h3>⚙️ Localhost Environment Settings</h3>
            <div class="form-group">
                <label for="lh_userid">User ID:</label>
                <input type="text" id="lh_userid" placeholder="Enter User ID" required>
            </div>
            <div class="form-group">
                <label for="lh_firmid">Firm ID:</label>
                <input type="text" id="lh_firmid" placeholder="Enter Firm ID" value="5" required>
            </div>
            <div class="btn-group">
                <button type="button" class="btn-cancel" id="lhCancelBtn">Cancel</button>
                <button type="button" class="btn-submit" id="lhSubmitBtn">Save & Reload</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    // Insert Settings Icon next to the main header
    document.addEventListener('DOMContentLoaded', () => {
        const header = document.querySelector('.container h1');
        if (header) {
            const settingsBtn = document.createElement('button');
            settingsBtn.type = 'button';
            settingsBtn.className = 'lh-settings-btn';
            settingsBtn.title = 'Change Localhost IDs';
            settingsBtn.innerHTML = '⚙️';
            settingsBtn.addEventListener('click', () => {
                openPopup();
            });
            header.appendChild(settingsBtn);
        }

        // Check if cookies are set. If not, auto-open popup on start
        const userid = getCookie('userid');
        const firmid = getCookie('firmid');
        if (!userid || !firmid) {
            openPopup();
        }
    });

    const lhUseridInput = document.getElementById('lh_userid');
    const lhFirmidInput = document.getElementById('lh_firmid');
    const lhSettingsOverlay = document.getElementById('lhSettingsOverlay');

    function openPopup() {
        lhUseridInput.value = getCookie('userid') || '';
        lhFirmidInput.value = getCookie('firmid') || '5';
        lhSettingsOverlay.classList.add('active');
    }

    function closePopup() {
        lhSettingsOverlay.classList.remove('active');
    }

    document.getElementById('lhCancelBtn').addEventListener('click', closePopup);
    document.getElementById('lhSubmitBtn').addEventListener('click', () => {
        const uid = lhUseridInput.value.trim();
        const fid = lhFirmidInput.value.trim() || '5';

        if (!uid) {
            alert('Please enter a User ID');
            return;
        }

        setCookie('userid', uid);
        setCookie('firmid', fid);
        closePopup();
        
        // Reload page to apply new cookies
        window.location.reload();
    });

    // Close on clicking overlay outside the popup
    lhSettingsOverlay.addEventListener('click', (e) => {
        if (e.target === lhSettingsOverlay) {
            closePopup();
        }
    });
})();
