// UI增强器 - 自动应用现代化美化效果

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 延迟执行以确保Streamlit组件已加载
    setTimeout(() => {
        enhanceUI();
        setupDynamicEnhancements();
    }, 1000);
});

// 主要UI增强函数
function enhanceUI() {
    enhanceCards();
    enhanceButtons();
    enhanceInputs();
    enhanceMessages();
    addLoadingAnimations();
    addHoverEffects();
    addScrollAnimations();
}

// 增强卡片效果
function enhanceCards() {
    const cards = document.querySelectorAll('.stBlock, .element-container');
    cards.forEach(card => {
        if (!card.classList.contains('enhanced-card') && 
            !card.closest('.stSidebar') &&
            !card.closest('.stChatMessage')) {
            card.classList.add('enhanced-card');
            
            // 添加悬停效果
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-5px) scale(1.02)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        }
    });
}

// 增强按钮效果
function enhanceButtons() {
    const buttons = document.querySelectorAll('button, .stButton > button, .stDownloadButton > button');
    buttons.forEach(button => {
        if (!button.classList.contains('enhanced-button')) {
            button.classList.add('enhanced-button');
            
            // 添加点击波纹效果
            button.addEventListener('click', function(e) {
                createRipple(e, this);
            });
            
            // 添加悬停音效（可选）
            button.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-3px) scale(1.05)';
            });
            
            button.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        }
    });
}

// 增强输入框效果
function enhanceInputs() {
    const inputs = document.querySelectorAll('input, textarea, .stTextInput input, .stTextArea textarea');
    inputs.forEach(input => {
        if (!input.classList.contains('enhanced-input')) {
            input.classList.add('enhanced-input');
            
            // 添加聚焦动画
            input.addEventListener('focus', function() {
                this.style.transform = 'scale(1.02)';
                this.style.boxShadow = '0 0 0 4px rgba(126, 182, 227, 0.15)';
            });
            
            input.addEventListener('blur', function() {
                this.style.transform = 'scale(1)';
                this.style.boxShadow = 'none';
            });
        }
    });
}

// 增强消息效果
function enhanceMessages() {
    const messages = document.querySelectorAll('.stChatMessage');
    messages.forEach(message => {
        if (!message.classList.contains('enhanced-message')) {
            message.classList.add('enhanced-message');
            
            // 判断消息类型
            if (message.getAttribute('data-testid') === 'stChatMessage-user') {
                message.classList.add('user');
            } else if (message.getAttribute('data-testid') === 'stChatMessage-assistant') {
                message.classList.add('assistant');
            }
            
            // 添加进入动画
            message.style.opacity = '0';
            message.style.transform = 'translateY(20px) scale(0.95)';
            
            setTimeout(() => {
                message.style.transition = 'all 0.5s ease-out';
                message.style.opacity = '1';
                message.style.transform = 'translateY(0) scale(1)';
            }, 100);
        }
    });
}

// 添加加载动画
function addLoadingAnimations() {
    // 为加载中的元素添加动画
    const loadingElements = document.querySelectorAll('.stSpinner, .stProgress');
    loadingElements.forEach(element => {
        element.classList.add('enhanced-loader');
    });
}

// 添加悬停效果
function addHoverEffects() {
    // 为可交互元素添加悬停效果
    const interactiveElements = document.querySelectorAll('.stSelectbox, .stMultiSelect, .stSlider');
    interactiveElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 4px 15px rgba(126, 182, 227, 0.15)';
        });
        
        element.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = 'none';
        });
    });
}

// 添加滚动动画
function addScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0) scale(1)';
            }
        });
    }, observerOptions);
    
    // 观察所有主要内容元素
    const elementsToObserve = document.querySelectorAll('.stBlock, .element-container');
    elementsToObserve.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px) scale(0.95)';
        element.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
        observer.observe(element);
    });
}

// 创建波纹效果
function createRipple(event, element) {
    const ripple = document.createElement('div');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${event.clientX - rect.left - size / 2}px`;
    ripple.style.top = `${event.clientY - rect.top - size / 2}px`;
    ripple.classList.add('ripple-effect');
    
    // 添加波纹样式
    ripple.style.position = 'absolute';
    ripple.style.borderRadius = '50%';
    ripple.style.background = 'rgba(255, 255, 255, 0.6)';
    ripple.style.transform = 'scale(0)';
    ripple.style.animation = 'ripple-animation 0.6s linear';
    ripple.style.pointerEvents = 'none';
    
    element.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

// 设置动态增强
function setupDynamicEnhancements() {
    // 监听DOM变化，为新元素应用增强效果
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // 为新添加的元素应用增强效果
                        setTimeout(() => {
                            enhanceNewElements(node);
                        }, 100);
                    }
                });
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

// 为新元素应用增强效果
function enhanceNewElements(container) {
    // 增强新的按钮
    const newButtons = container.querySelectorAll('button');
    newButtons.forEach(button => {
        if (!button.classList.contains('enhanced-button')) {
            button.classList.add('enhanced-button');
            button.addEventListener('click', function(e) {
                createRipple(e, this);
            });
        }
    });
    
    // 增强新的输入框
    const newInputs = container.querySelectorAll('input, textarea');
    newInputs.forEach(input => {
        if (!input.classList.contains('enhanced-input')) {
            input.classList.add('enhanced-input');
        }
    });
    
    // 增强新的消息
    const newMessages = container.querySelectorAll('.stChatMessage');
    newMessages.forEach(message => {
        if (!message.classList.contains('enhanced-message')) {
            message.classList.add('enhanced-message');
            
            // 添加进入动画
            message.style.opacity = '0';
            message.style.transform = 'translateY(20px) scale(0.95)';
            
            setTimeout(() => {
                message.style.transition = 'all 0.5s ease-out';
                message.style.opacity = '1';
                message.style.transform = 'translateY(0) scale(1)';
            }, 100);
        }
    });
}

// 添加CSS动画样式
function addAnimationStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple-animation {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
        
        .enhanced-card {
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .enhanced-button {
            position: relative;
            overflow: hidden;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .enhanced-input {
            transition: all 0.3s ease;
        }
        
        .enhanced-message {
            transition: all 0.5s ease-out;
        }
    `;
    document.head.appendChild(style);
}

// 初始化动画样式
addAnimationStyles();