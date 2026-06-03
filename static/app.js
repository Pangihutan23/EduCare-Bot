/* =============================================================================
   app.js
   Logika Frontend SPA — Sistem Pakar Pendamping Belajar v2.0
   ============================================================================= */

// --- Inisialisasi Sesi Pengguna ---
let userId = localStorage.getItem('pakar_belajar_user_id');
if (!userId) {
    // Generate 8-digit random number (mirip ID Telegram)
    userId = String(Math.floor(10000000 + Math.random() * 90000000));
    localStorage.setItem('pakar_belajar_user_id', userId);
}

// Tampilkan ID di sidebar
document.getElementById('user-session-id').innerText = `ID: ${userId}`;

// Global State
let activePanel = 'panel-chat';
let activeState = null; // Menyimpan state FSM aktif dari server

// --- Utilitas: Parser Markdown Sederhana ---
function parseMarkdown(text) {
    if (!text) return "";
    
    // Normalisasi newline
    let html = text;
    
    // Bold: **text** atau *text*
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<strong>$1</strong>');
    
    // Italic: _text_
    html = html.replace(/_(.*?)_/g, '<em>$1</em>');
    
    // Inline Code: `code`
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');
    
    // Newline to BR
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

// Dapatkan waktu saat ini format HH:MM
function getFormattedTime() {
    const now = new Date();
    const hrs = String(now.getHours()).padStart(2, '0');
    const mins = String(now.getMinutes()).padStart(2, '0');
    return `${hrs}:${mins}`;
}

// --- Manajemen Toast Notifikasi ---
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container-element');
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'fa-info-circle';
    let title = 'Pemberitahuan';
    
    if (type === 'danger') {
        icon = 'fa-triangle-exclamation';
        title = 'Peringatan Deadline';
    } else if (type === 'warning') {
        icon = 'fa-bell';
        title = 'Pengingat Deadline';
    } else if (type === 'success') {
        icon = 'fa-circle-check';
        title = 'Berhasil';
    }
    
    toast.innerHTML = `
        <div class="toast-icon"><i class="fa-solid ${icon}"></i></div>
        <div class="toast-body">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${parseMarkdown(message)}</div>
        </div>
        <button class="toast-close"><i class="fa-solid fa-xmark"></i></button>
    `;
    
    container.appendChild(toast);
    
    // Play scale effect on badge
    const badge = document.getElementById('task-badge');
    badge.style.transform = 'scale(1.2)';
    setTimeout(() => badge.style.transform = 'scale(1)', 300);
    
    // Close button event
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        setTimeout(() => toast.remove(), 300);
    });
    
    // Auto remove
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(40px)';
            setTimeout(() => toast.remove(), 300);
        }
    }, 6000);
}

// --- Navigasi Tab SPA ---
const menuItems = document.querySelectorAll('.menu-item');
const panels = document.querySelectorAll('.content-panel');

menuItems.forEach(item => {
    item.addEventListener('click', () => {
        const target = item.getAttribute('data-target');
        
        // Update menu active class
        menuItems.forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        
        // Update panel active class
        panels.forEach(p => p.classList.remove('active'));
        const activeP = document.getElementById(target);
        activeP.classList.add('active');
        
        activePanel = target;
        loggerInfo(`Berpindah ke panel: ${target}`);
        
        // Jika berpindah ke board tugas, ambil data terbaru
        if (target === 'panel-tasks') {
            fetchTasks();
        }
    });
});

// Logger Helper
function loggerInfo(msg) {
    console.log(`[PakarBelajar UI] ${msg}`);
}

// --- Ruang Obrolan (Chat Room) ---
const chatMessagesContainer = document.getElementById('chat-messages-container');
const chatInlineButtons = document.getElementById('chat-inline-buttons');
const chatInputField = document.getElementById('chat-input-field');
const btnChatSend = document.getElementById('btn-chat-send');
const chatTypingIndicator = document.getElementById('chat-typing-indicator');
const btnChatBatal = document.getElementById('btn-chat-batal');

// Update visibilitas tombol Batal
function updateBatalButton(state) {
    activeState = state;
    if (state) {
        btnChatBatal.classList.add('active');
    } else {
        btnChatBatal.classList.remove('active');
    }
}

// Sleep helper untuk delay mengetik
const sleep = ms => new Promise(res => setTimeout(res, ms));

// Menggulung chat ke bawah
function scrollChatToBottom() {
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
}

// Menambahkan gelembung obrolan
function appendChatMessage(sender, text, time = null) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;
    
    const avatar = sender === 'bot' ? '<i class="fa-solid fa-comments"></i>' : '<i class="fa-solid fa-user"></i>';
    const timestamp = time || getFormattedTime();
    
    bubble.innerHTML = `
        <div class="bubble-avatar">${avatar}</div>
        <div class="bubble-content">
            <div class="bubble-text">${parseMarkdown(text)}</div>
            <span class="bubble-time">${timestamp}</span>
        </div>
    `;
    
    chatMessagesContainer.appendChild(bubble);
    scrollChatToBottom();
}

// Menampilkan tombol inline
function renderInlineButtons(buttons) {
    chatInlineButtons.innerHTML = '';
    if (!buttons || buttons.length === 0) return;
    
    buttons.forEach(btn => {
        const buttonElement = document.createElement('button');
        buttonElement.className = 'inline-btn';
        
        let btnText = btn.text;
        let iconHtml = '';
        
        // Remove potential emojis and format text / icons
        if (btnText.includes('Diagnosa Masalah')) {
            btnText = 'Diagnosa Masalah';
            iconHtml = '<i class="fa-solid fa-brain" style="color: #ec4899;"></i>';
        } else if (btnText.includes('Manajemen Tugas') || btnText.includes('Tugas')) {
            btnText = btnText.replace('📋 ', '').replace('➕ ', '').replace('🗑️ ', '').replace('💥 ', '');
            let iconColor = '#f97316';
            let iconClass = 'fa-solid fa-clipboard-list';
            if (btn.callback_data === 'tugas_tambah') {
                iconClass = 'fa-solid fa-plus';
                iconColor = '#10b981';
            } else if (btn.callback_data === 'tugas_hapus') {
                iconClass = 'fa-solid fa-trash-can';
                iconColor = '#ef4444';
            }
            iconHtml = `<i class="${iconClass}" style="color: ${iconColor};"></i>`;
        } else if (btnText.includes('Bantuan') || btnText.includes('Bantuan & Info')) {
            btnText = 'Bantuan & Info';
            iconHtml = '<i class="fa-solid fa-circle-info" style="color: #ffffff;"></i>';
        } else if (btnText.includes('Cek Pengingat') || btnText.includes('Cek Reminder') || btnText.includes('Reminder')) {
            btnText = 'Cek Pengingat';
            iconHtml = '<i class="fa-solid fa-bell" style="color: #eab308;"></i>';
        } else if (btnText.includes('Kembali')) {
            btnText = 'Kembali';
            iconHtml = '<i class="fa-solid fa-arrow-left" style="color: #94a3b8;"></i>';
        } else if (btnText.includes('Batal')) {
            btnText = 'Batal';
            iconHtml = '<i class="fa-solid fa-xmark" style="color: #ef4444;"></i>';
        } else if (btnText.includes('Ya, Hapus Semua')) {
            btnText = 'Ya, Hapus Semua';
            iconHtml = '<i class="fa-solid fa-circle-exclamation" style="color: #ef4444;"></i>';
        }
        
        buttonElement.innerHTML = `${iconHtml}<span>${btnText}</span>`;
        buttonElement.addEventListener('click', () => {
            // Bersihkan keyboard inline saat diklik
            chatInlineButtons.innerHTML = '';
            // Tampilkan pesan klik user
            appendChatMessage('user', btn.text);
            // Jalankan callback ke backend
            sendCallbackQuery(btn.callback_data);
        });
        chatInlineButtons.appendChild(buttonElement);
    });
    scrollChatToBottom();
}

// Menampilkan/menyembunyikan indikator mengetik
function setTyping(isTyping) {
    if (isTyping) {
        chatTypingIndicator.classList.add('active');
        scrollChatToBottom();
    } else {
        chatTypingIndicator.classList.remove('active');
    }
}

// Mengirim Callback Query
async function sendCallbackQuery(callbackData) {
    setTyping(true);
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId: userId, callbackData: callbackData })
        });
        
        const data = await response.json();
        setTyping(false);
        
        if (data.replies) {
            for (let i = 0; i < data.replies.length; i++) {
                const reply = data.replies[i];
                setTyping(true);
                // Hitung delay mengetik alami berdasarkan panjang teks (min 400ms, max 1400ms)
                const delay = Math.min(Math.max(reply.text.length * 6, 400), 1400);
                await sleep(delay);
                setTyping(false);
                
                appendChatMessage('bot', reply.text);
                if (reply.buttons && i === data.replies.length - 1) {
                    renderInlineButtons(reply.buttons);
                }
            }
        }
        updateBatalButton(data.state);
        
        // Refresh tasks jika aksi menyangkut manipulasi data tugas
        if (callbackData.startsWith('tugas_') || callbackData === 'konfirmasi_hapus_semua') {
            fetchTasks();
        }
    } catch (error) {
        setTyping(false);
        appendChatMessage('bot', '❌ Gagal terhubung ke server. Pastikan server Flask Anda berjalan.');
        console.error(error);
    }
}

// Mengirim Pesan Teks
async function sendTextMessage(messageText) {
    if (!messageText.trim()) return;
    
    // Tampilkan pesan user di screen
    appendChatMessage('user', messageText);
    chatInputField.value = '';
    
    setTyping(true);
    chatInlineButtons.innerHTML = ''; // Hapus tombol inline sebelumnya
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userId: userId, message: messageText })
        });
        
        const data = await response.json();
        setTyping(false);
        
        if (data.replies) {
            for (let i = 0; i < data.replies.length; i++) {
                const reply = data.replies[i];
                setTyping(true);
                // Hitung delay mengetik alami berdasarkan panjang teks (min 400ms, max 1400ms)
                const delay = Math.min(Math.max(reply.text.length * 6, 400), 1400);
                await sleep(delay);
                setTyping(false);
                
                appendChatMessage('bot', reply.text);
                if (reply.buttons && i === data.replies.length - 1) {
                    renderInlineButtons(reply.buttons);
                }
            }
        }
        updateBatalButton(data.state);
        fetchTasks(); // Refresh board tugas barangkali ada tugas ditambahkan
    } catch (error) {
        setTyping(false);
        appendChatMessage('bot', '❌ Gagal terhubung ke server. Pastikan server Flask Anda berjalan.');
        console.error(error);
    }
}

// Event Listeners Chat
btnChatSend.addEventListener('click', () => {
    sendTextMessage(chatInputField.value);
});

chatInputField.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendTextMessage(chatInputField.value);
    }
});

btnChatBatal.addEventListener('click', () => {
    sendTextMessage('/batal');
});

document.getElementById('btn-clear-chat').addEventListener('click', () => {
    if (confirm('Apakah Anda yakin ingin membersihkan log percakapan di layar?')) {
        chatMessagesContainer.innerHTML = '';
        chatInlineButtons.innerHTML = '';
        // Inisialisasi ulang
        sendCallbackQuery('menu_utama');
    }
});


// --- Papan Tugas (Task Board) ---
const taskFormContainer = document.getElementById('task-form-container');
const btnToggleTaskForm = document.getElementById('btn-toggle-task-form');
const btnCloseTaskForm = document.getElementById('btn-close-task-form');
const btnCancelTaskForm = document.getElementById('btn-cancel-task-form');
const addTaskForm = document.getElementById('add-task-form');
const tasksCardsGrid = document.getElementById('tasks-cards-grid');
const tasksEmptyState = document.getElementById('tasks-empty-state');

// Toggle Form visibility
btnToggleTaskForm.addEventListener('click', () => {
    taskFormContainer.classList.toggle('active');
    if (taskFormContainer.classList.contains('active')) {
        document.getElementById('form-task-name').focus();
    }
});

function closeTaskForm() {
    taskFormContainer.classList.remove('active');
    addTaskForm.reset();
}

btnCloseTaskForm.addEventListener('click', closeTaskForm);
btnCancelTaskForm.addEventListener('click', closeTaskForm);

// Submit Form Tugas Baru
addTaskForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const namaTugas = document.getElementById('form-task-name').value.trim();
    const mataKuliah = document.getElementById('form-task-course').value.trim();
    const deadline = document.getElementById('form-task-deadline').value.trim();
    const catatan = document.getElementById('form-task-notes').value.trim();
    
    // Validasi format DD/MM/YYYY sederhana
    const dateRegex = /^\d{2}\/\d{2}\/\d{4}$/;
    if (!dateRegex.test(deadline)) {
        showToast('Format deadline salah! Harap gunakan format DD/MM/YYYY (contoh: 25/05/2026)', 'danger');
        return;
    }
    
    try {
        const response = await fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                userId: userId,
                nama_tugas: namaTugas,
                mata_kuliah: mataKuliah,
                deadline: deadline,
                catatan: catatan
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`Tugas "${namaTugas}" berhasil disimpan!`, 'success');
            closeTaskForm();
            fetchTasks();
            // Kirim pesan sukses ke chat log agar tersinkronisasi
            appendChatMessage('bot', `➕ **Tugas baru ditambahkan via formulir:**\n📌 **${namaTugas}** (${mataKuliah})\n📅 Deadline: ${deadline}`);
        } else {
            showToast(`Gagal menyimpan: ${data.error}`, 'danger');
        }
    } catch (error) {
        showToast('Gagal terhubung ke server untuk menyimpan tugas.', 'danger');
        console.error(error);
    }
});

// Hapus Tugas
async function deleteTask(taskId, taskName) {
    if (!confirm(`Apakah Anda yakin ingin menghapus tugas "${taskName}"?`)) return;
    
    try {
        const response = await fetch(`/api/tasks/${taskId}?userId=${userId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        if (data.success) {
            showToast(`Tugas "${taskName}" berhasil dihapus.`, 'success');
            fetchTasks();
            // Infokan juga di chat log
            appendChatMessage('bot', `🗑️ **Tugas dihapus via papan:**\n❌ **${taskName}** (ID: \`${taskId}\`)`);
        } else {
            showToast(`Gagal menghapus tugas: ${data.error}`, 'danger');
        }
    } catch (error) {
        showToast('Gagal terhubung ke server untuk menghapus tugas.', 'danger');
        console.error(error);
    }
}

// Mengambil Tugas & Mengupdate UI
async function fetchTasks() {
    try {
        const response = await fetch(`/api/tasks?userId=${userId}`);
        const data = await response.json();
        const tasks = data.tasks || [];
        
        // Update stats
        const total = tasks.length;
        let danger = 0;
        let warning = 0;
        let safe = 0;
        
        const now = new Date();
        now.setHours(0,0,0,0);
        
        // Hapus kartu lama selain empty-state
        const cards = tasksCardsGrid.querySelectorAll('.task-card');
        cards.forEach(c => c.remove());
        
        if (total === 0) {
            tasksEmptyState.style.display = 'flex';
        } else {
            tasksEmptyState.style.display = 'none';
            
            tasks.forEach(t => {
                // Tentukan status deadline
                let statusClass = 'status-success';
                let statusText = 'Aman';
                
                // Parse deadline DD/MM/YYYY
                const parts = t.deadline.split('/');
                if (parts.length === 3) {
                    const dlDate = new Date(parts[2], parts[1] - 1, parts[0]);
                    dlDate.setHours(0,0,0,0);
                    const diffDays = Math.ceil((dlDate - now) / (1000 * 60 * 60 * 24));
                    
                    if (diffDays < 0) {
                        statusClass = 'status-danger';
                        statusText = 'Terlewat!';
                        danger++;
                    } else if (diffDays === 0) {
                        statusClass = 'status-danger';
                        statusText = '🚨 Hari Ini!';
                        danger++;
                    } else if (diffDays === 1) {
                        statusClass = 'status-danger';
                        statusText = '🔴 Besok!';
                        danger++;
                    } else if (diffDays <= 3) {
                        statusClass = 'status-warning';
                        statusText = `⚠️ ${diffDays} hari lagi`;
                        warning++;
                    } else {
                        statusClass = 'status-success';
                        statusText = `🟢 ${diffDays} hari lagi`;
                        safe++;
                    }
                } else {
                    safe++;
                }
                
                const card = document.createElement('div');
                card.className = `task-card ${statusClass}`;
                card.innerHTML = `
                    <div class="task-card-header">
                        <h4>${t.nama_tugas}</h4>
                        <span class="badge">${statusText}</span>
                    </div>
                    <div class="task-meta">
                        <div><i class="fa-solid fa-book"></i> <span>${t.mata_kuliah}</span></div>
                        <div><i class="fa-solid fa-calendar-day"></i> <span>Tenggat: ${t.deadline}</span></div>
                    </div>
                    ${t.catatan ? `<div class="task-card-notes">${t.catatan}</div>` : ''}
                    <div class="task-card-actions">
                        <span class="task-id">ID: <code>${t.id}</code></span>
                        <button class="btn-task-delete" title="Hapus Tugas">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </div>
                `;
                
                // Event Hapus
                card.querySelector('.btn-task-delete').addEventListener('click', () => {
                    deleteTask(t.id, t.nama_tugas);
                });
                
                tasksCardsGrid.appendChild(card);
            });
        }
        
        // Render Dashboard Stats
        document.getElementById('stat-total-val').innerText = total;
        document.getElementById('stat-alert-val').innerText = danger;
        document.getElementById('stat-warning-val').innerText = warning;
        document.getElementById('stat-safe-val').innerText = safe;
        
        // Render Badge Sidebar
        const badge = document.getElementById('task-badge');
        badge.innerText = total;
        if (danger > 0) {
            badge.style.background = 'var(--color-red)';
        } else if (warning > 0) {
            badge.style.background = 'var(--color-yellow)';
        } else {
            badge.style.background = 'var(--color-primary)';
        }
        
    } catch (error) {
        console.error('Gagal mengambil tugas dari server:', error);
    }
}


// --- Sistem Polling Notifikasi & Peringatan ---
async function pollNotifications() {
    try {
        const response = await fetch(`/api/notifications?userId=${userId}`);
        const data = await response.json();
        
        if (data.notifications && data.notifications.length > 0) {
            data.notifications.forEach(note => {
                loggerInfo(`Notifikasi baru diterima: ${note.message}`);
                
                // Klasifikasikan tingkat bahaya untuk tipe toast
                let type = 'info';
                if (note.message.includes('H-0') || note.message.includes('🚨')) {
                    type = 'danger';
                } else if (note.message.includes('H-1') || note.message.includes('H-3') || note.message.includes('⚠️')) {
                    type = 'warning';
                } else if (note.message.includes('berhasil')) {
                    type = 'success';
                }
                
                // 1. Tampilkan notifikasi pop-up Toast
                showToast(note.message, type);
                
                // 2. Masukkan ke dalam room chat log agar terekam sejarahnya
                appendChatMessage('bot', `🔔 **PENGINGAT DEADLINE OTOMATIS**\n\n${note.message}`);
            });
            
            // Re-fetch tasks jika ada notifikasi deadline mendekat
            fetchTasks();
        }
    } catch (error) {
        console.error('Gagal menarik notifikasi:', error);
    }
}

// --- Inisialisasi Halaman ---
window.addEventListener('DOMContentLoaded', () => {
    // 1. Jalankan polling notifikasi setiap 8 detik
    pollNotifications(); // Run immediately on load
    setInterval(pollNotifications, 8000);
    
    // 2. Fetch data tugas awal untuk badge sidebar
    fetchTasks();
    
    // 3. Muat percakapan awal (Kirim /start ke bot untuk menyapa)
    appendChatMessage('bot', '🤖 Menghubungkan ke asisten akademik...');
    setTyping(true);
    setTimeout(() => {
        chatMessagesContainer.innerHTML = '';
        sendCallbackQuery('menu_utama');
    }, 1200);
});
