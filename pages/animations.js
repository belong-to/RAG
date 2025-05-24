// 页面动画效果增强脚本

// 页面加载完成后执行动画
document.addEventListener('DOMContentLoaded', () => {
    // 添加页面加载动画类
    document.body.classList.add('page-loaded');

    // 为所有按钮添加波纹效果
    addRippleEffect();

    // 为元素添加滑入动画
    addScrollAnimations();

    // 为上传区域添加拖拽动画
    setupDragAndDrop();

    // 添加浮动动画
    addFloatingAnimations();

    // 添加打字机效果
    addTypewriterEffect();

    // 添加粒子效果
    addParticleEffect();
});

// 添加浮动动画
function addFloatingAnimations() {
    const floatingElements = document.querySelectorAll('.stButton, .stDownloadButton');
    floatingElements.forEach((element, index) => {
        element.style.animationDelay = `${index * 0.2}s`;
        element.classList.add('floating-element');
    });
}

// 添加打字机效果
function addTypewriterEffect() {
    const titles = document.querySelectorAll('h1, h2, h3');
    titles.forEach(title => {
        const text = title.textContent;
        title.textContent = '';
        title.style.borderRight = '2px solid #7eb6e3';
        
        let i = 0;
        const typeWriter = () => {
            if (i < text.length) {
                title.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, 100);
            } else {
                setTimeout(() => {
                    title.style.borderRight = 'none';
                }, 1000);
            }
        };
        
        setTimeout(typeWriter, 500);
    });
}

// 添加粒子效果
function addParticleEffect() {
    const particleContainer = document.createElement('div');
    particleContainer.className = 'particle-container';
    document.body.appendChild(particleContainer);
    
    for (let i = 0; i < 20; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 10 + 's';
        particle.style.animationDuration = (Math.random() * 10 + 10) + 's';
        particleContainer.appendChild(particle);
    }
}

// 添加波纹效果
function addRippleEffect() {
    const buttons = document.querySelectorAll('button, .stButton>button, .stDownloadButton>button');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('div');
            ripple.classList.add('ripple');
            
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            
            ripple.style.width = ripple.style.height = `${size}px`;
            ripple.style.left = `${e.clientX - rect.left - size/2}px`;
            ripple.style.top = `${e.clientY - rect.top - size/2}px`;
            
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
}

// 添加滚动动画
function addScrollAnimations() {
    const elements = document.querySelectorAll('.element-container, .stMarkdown, .stAlert');
    
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('scroll-visible');
                }
            });
        },
        { threshold: 0.1 }
    );

    elements.forEach(element => {
        element.classList.add('scroll-hidden');
        observer.observe(element);
    });
}

// 设置拖拽上传动画
function setupDragAndDrop() {
    const uploadArea = document.querySelector('.upload-area');
    if (!uploadArea) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.remove('drag-over');
        });
    });
}