document.addEventListener("DOMContentLoaded", () => {
    const calendarContainer = document.getElementById('calendly-days');
    const bookingModal = document.getElementById('booking-modal');
    const closeModal = document.getElementById('close-modal');
    
    const step1 = document.getElementById('step-1');
    const step2 = document.getElementById('step-2');
    
    const startTimeInput = document.getElementById('start_time');
    const endTimeInput = document.getElementById('end_time');
    const serviceNameInput = document.getElementById('service_name');
    const priceInput = document.getElementById('price');
    const paypalTransactionInput = document.getElementById('paypal_transaction_id');
    
    const modalTimeDisplay = document.getElementById('modal-time-display');
    const modalServiceName = document.getElementById('modal-service-name');
    const modalPriceDisplay = document.getElementById('modal-price-display');
    
    const timeSlotsSidebar = document.getElementById('calendly-time-slots');
    const selectedDateDisplay = document.getElementById('selected-date-display');
    const timeSlotsContainer = document.getElementById('time-slots-container');
    
    const bookingForm = document.getElementById('booking-form');
    
    const prevMonthBtn = document.getElementById('prev-month');
    const nextMonthBtn = document.getElementById('next-month');
    const monthYearDisplay = document.getElementById('month-year-display');
    
    let currentService = null;
    let currentPrice = 0;
    
    let currentDisplayMonth = new Date().getMonth();
    let currentDisplayYear = new Date().getFullYear();
    const today = new Date();
    today.setHours(0,0,0,0);
    
    let selectedDate = null;

    // Attach event listeners to all "Book Now" buttons
    document.querySelectorAll('.book-service-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (typeof isLoggedIn !== 'undefined' && !isLoggedIn) {
                window.location.href = '/login';
                return;
            }
            currentService = e.target.getAttribute('data-service');
            currentPrice = e.target.getAttribute('data-price');
            
            modalServiceName.innerText = currentService;
            modalPriceDisplay.innerText = currentPrice;
            serviceNameInput.value = currentService;
            priceInput.value = currentPrice;
            
            // Reset to step 1
            step1.classList.remove('hidden');
            step2.classList.add('hidden');
            timeSlotsSidebar.classList.add('hidden');
            selectedDate = null;
            
            currentDisplayMonth = today.getMonth();
            currentDisplayYear = today.getFullYear();
            
            bookingModal.classList.remove('hidden');
            
            if (calendarContainer && typeof availabilityData !== 'undefined') {
                renderMonthCalendar();
            }
        });
    });

    if (closeModal) {
        closeModal.addEventListener('click', () => {
            bookingModal.classList.add('hidden');
            document.getElementById('paypal-button-container').innerHTML = '';
        });
    }
    
    if (prevMonthBtn) {
        prevMonthBtn.addEventListener('click', () => {
            currentDisplayMonth--;
            if (currentDisplayMonth < 0) {
                currentDisplayMonth = 11;
                currentDisplayYear--;
            }
            renderMonthCalendar();
        });
    }
    
    if (nextMonthBtn) {
        nextMonthBtn.addEventListener('click', () => {
            currentDisplayMonth++;
            if (currentDisplayMonth > 11) {
                currentDisplayMonth = 0;
                currentDisplayYear++;
            }
            renderMonthCalendar();
        });
    }

    function renderMonthCalendar() {
        calendarContainer.innerHTML = '';
        timeSlotsSidebar.classList.add('hidden');
        
        const firstDay = new Date(currentDisplayYear, currentDisplayMonth, 1);
        const lastDay = new Date(currentDisplayYear, currentDisplayMonth + 1, 0);
        
        // Month Year display
        const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
        monthYearDisplay.innerText = `${monthNames[currentDisplayMonth]} ${currentDisplayYear}`;
        
        // Disable prev button if viewing current month
        if (currentDisplayYear === today.getFullYear() && currentDisplayMonth <= today.getMonth()) {
            prevMonthBtn.style.opacity = '0.3';
            prevMonthBtn.style.pointerEvents = 'none';
        } else {
            prevMonthBtn.style.opacity = '1';
            prevMonthBtn.style.pointerEvents = 'auto';
        }
        
        // Calculate offset for first day (0=Sun, 1=Mon... we want Mon=0, Sun=6)
        let startOffset = firstDay.getDay() - 1;
        if (startOffset < 0) startOffset = 6;
        
        // Empty cells for days before the 1st
        for (let i = 0; i < startOffset; i++) {
            const emptyCell = document.createElement('div');
            calendarContainer.appendChild(emptyCell);
        }
        
        // Render days
        for (let i = 1; i <= lastDay.getDate(); i++) {
            const cellDate = new Date(currentDisplayYear, currentDisplayMonth, i);
            const dayOfWeek = cellDate.getDay();
            
            const cell = document.createElement('div');
            cell.className = 'day-cell';
            
            const numSpan = document.createElement('div');
            numSpan.className = 'day-num';
            numSpan.innerText = i;
            cell.appendChild(numSpan);
            
            // Check past
            if (cellDate < today) {
                cell.classList.add('disabled');
            } else {
                // Check availability
                const availBlocks = availabilityData.filter(a => a.day === dayOfWeek);
                if (availBlocks.length > 0) {
                    cell.classList.add('available');
                    
                    // Click handler to select date and show slots
                    cell.addEventListener('click', () => {
                        // Remove selected from all
                        document.querySelectorAll('.day-cell.selected').forEach(c => c.classList.remove('selected'));
                        cell.classList.add('selected');
                        selectedDate = cellDate;
                        renderTimeSlots(cellDate, availBlocks);
                    });
                } else {
                    // Not available
                    cell.style.color = '#1a1a1a'; // normal color, no blue circle
                }
            }
            
            // Check today
            if (cellDate.getTime() === today.getTime()) {
                cell.classList.add('today');
            }
            
            calendarContainer.appendChild(cell);
        }
    }
    
    function renderTimeSlots(date, availBlocks) {
        timeSlotsContainer.innerHTML = '';
        
        const options = { weekday: 'long', month: 'long', day: 'numeric' };
        selectedDateDisplay.innerText = date.toLocaleDateString(undefined, options);
        
        let hasSlots = false;
        
        availBlocks.forEach(block => {
            const startHour = parseInt(block.start.split(':')[0]);
            const endHour = parseInt(block.end.split(':')[0]);
            
            for (let h = startHour; h < endHour; h++) {
                const slotStart = new Date(date);
                slotStart.setHours(h, 0, 0, 0);
                
                const slotEnd = new Date(date);
                slotEnd.setHours(h + 1, 0, 0, 0);
                
                if (slotStart < new Date()) continue;
                
                hasSlots = true;
                const timeStr = slotStart.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                
                const slotBtn = document.createElement('button');
                slotBtn.className = 'slot-btn';
                slotBtn.innerText = timeStr;
                
                slotBtn.onclick = () => proceedToDetails(slotStart, slotEnd, timeStr, selectedDateDisplay.innerText);
                
                timeSlotsContainer.appendChild(slotBtn);
            }
        });
        
        if (!hasSlots) {
            timeSlotsContainer.innerHTML = '<p style="color:#666;">No slots available today.</p>';
        }
        
        timeSlotsSidebar.classList.remove('hidden');
    }

    function proceedToDetails(slotStart, slotEnd, timeStr, dateStr) {
        startTimeInput.value = slotStart.toISOString();
        endTimeInput.value = slotEnd.toISOString();
        modalTimeDisplay.innerText = `${dateStr} at ${timeStr}`;
        
        step1.classList.add('hidden');
        step2.classList.remove('hidden');
        
        renderPayPal();
    }
    
    function renderPayPal() {
        const container = document.getElementById('paypal-button-container');
        container.innerHTML = '';
        
        if (typeof paypal !== 'undefined') {
            paypal.Buttons({
                createOrder: function(data, actions) {
                    const name = document.getElementById('client_name').value;
                    const email = document.getElementById('client_email').value;
                    if (!name || !email) {
                        alert("Please enter your name and email before paying.");
                        return;
                    }
                    
                    return actions.order.create({
                        purchase_units: [{
                            description: currentService,
                            amount: {
                                value: currentPrice
                            }
                        }]
                    });
                },
                onApprove: function(data, actions) {
                    return actions.order.capture().then(function(details) {
                        paypalTransactionInput.value = details.id;
                        bookingForm.submit();
                    });
                },
                onError: function(err) {
                    console.error("PayPal Error:", err);
                    alert("There was an error processing your payment.");
                }
            }).render('#paypal-button-container');
        } else {
            container.innerHTML = '<p style="color:red; font-weight:700;">PayPal SDK failed to load. Check your Client ID.</p>';
        }
    }
});
