        document.addEventListener("DOMContentLoaded", function () {

            // 演示数据：后续将由 Flask 后端提供
            let skills = [];
            let editingSkillId = null;
            let currentCategory = "全部";
            let currentPage = "hall";
            let currentSkill = null;
            let authMode = "login";
            let currentUser = null;

            const skillGrid = document.getElementById("skillGrid");
            //const recommendGrid = document.getElementById("recommendGrid");
            const searchInput = document.getElementById("searchInput");

            function showToast(message) {
                const toast = document.getElementById("toast");
                toast.textContent = message;
                toast.classList.add("show");

                window.clearTimeout(showToast.timer);
                showToast.timer = window.setTimeout(function () {
                    toast.classList.remove("show");
                }, 2500);
            }

            // 统一处理后端 API 请求
            async function apiRequest(url, method = "GET", data = null) {
                const options = {
                    method: method,
                    headers: {
                        "Content-Type": "application/json"
                    }
                };

                if (data) {
                    options.body = JSON.stringify(data);
                }

                const response = await fetch(url, options);

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.message || "请求失败，请稍后重试");
                }

                return result;
            }

            function openModal(id) {
                const modal = document.getElementById(id);
                if (modal) modal.classList.add("show");
            }

            function closeModal(id) {
                const modal = document.getElementById(id);
                if (modal) modal.classList.remove("show");
            }

            function createSkillCard(skill) {
                return `
                    <article class="skill-card" data-id="${skill.id}">
                        <div class="skill-top">
                            <div class="skill-icon">${skill.icon}</div>
                            <span class="skill-category">${skill.category}</span>
                        </div>

                        <h3>${escapeHTML(skill.name)}</h3>
                        <p class="skill-description">${escapeHTML(skill.description)}</p>

                        <div class="skill-person">
                            <div class="person-info">
                                <div class="avatar">👤</div>
                                <div>
                                    <div class="person-name">${escapeHTML(skill.person)}</div>
                                    <div class="person-location">📍 ${escapeHTML(skill.location)}</div>
                                </div>
                            </div>
                            <span class="exchange-label">↔ 可交换</span>
                        </div>
                    </article>
                `;
            }

            function escapeHTML(value) {
                return String(value).replace(/[&<>"']/g, function (char) {
                    const map = {
                        "&": "&amp;",
                        "<": "&lt;",
                        ">": "&gt;",
                        '"': "&quot;",
                        "'": "&#039;"
                    };
                    return map[char];
                });
            }

            function renderSkills() {
                const keyword = searchInput.value.trim().toLowerCase();

                const filtered = skills.filter(function (skill) {
                    const matchesCategory =
                        currentCategory === "全部" ||
                        skill.category === currentCategory;

                    const matchesKeyword =
                        skill.name.toLowerCase().includes(keyword) ||
                        skill.description.toLowerCase().includes(keyword) ||
                        skill.person.toLowerCase().includes(keyword);

                    return matchesCategory && matchesKeyword;
                });

                if (filtered.length === 0) {
                    skillGrid.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-icon">🔎</div>
                            <h3>没有找到相关技能</h3>
                            <p>试试其他关键词或分类吧。</p>
                        </div>
                    `;
                    return;
                }

                skillGrid.innerHTML = filtered.map(createSkillCard).join("");
            }

            // 从后端获取技能列表
            async function loadSkills() {
                const result = await apiRequest("/api/skills/");

                skills = result.skills;

                renderSkills();
                renderRecommendations();
                renderProfile();
            }

            async function renderRecommendations() {
                const container = document.getElementById("recommendationsContainer");

                if (!container) {
                    return;
                }

                container.innerHTML = `
                    <p class="empty-message">正在寻找适合你的技能交换伙伴...</p>
                `;

                try {
                    const result = await apiRequest("/api/matching/");

                    if (!result.success) {
                        container.innerHTML = `
                            <p class="empty-message">暂时无法获取推荐</p>
                        `;
                        return;
                    }

                    const matches = result.matches || [];

                    if (matches.length === 0) {
                        container.innerHTML = `
                            <div class="empty-state">
                                <div class="empty-icon">🔍</div>
                                <h3>暂时没有匹配伙伴</h3>
                                <p>完善你的技能和学习需求，发现更多交换机会吧！</p>
                            </div>
                        `;
                        return;
                    }

                    container.innerHTML = "";

                    matches.forEach(function (match) {
                        const card = document.createElement("div");
                        card.className = "recommendation-card";

                        const header = document.createElement("div");
                        header.className = "recommendation-header";

                        const avatar = document.createElement("div");
                        avatar.className = "recommendation-avatar";
                        avatar.textContent = "👤";

                        const userInfo = document.createElement("div");
                        userInfo.className = "recommendation-user-info";

                        const username = document.createElement("h3");
                        username.textContent = match.username;

                        const matchType = document.createElement("span");
                        matchType.className = "match-badge";
                        matchType.textContent = match.match_type;

                        userInfo.appendChild(username);
                        userInfo.appendChild(matchType);

                        header.appendChild(avatar);
                        header.appendChild(userInfo);

                        const skills = document.createElement("div");
                        skills.className = "recommendation-skills";

                        const mySkill = document.createElement("p");
                        mySkill.textContent = "你能教：" + match.my_skill;

                        const theirSkill = document.createElement("p");
                        theirSkill.textContent = "对方能教：" + match.their_skill;

                        skills.appendChild(mySkill);
                        skills.appendChild(theirSkill);

                        card.appendChild(header);
                        card.appendChild(skills);

                        // 申请交换按钮
                        const applyButton = document.createElement("button");
                        applyButton.className = "apply-exchange-btn";
                        applyButton.textContent = "申请交换";

                        applyButton.addEventListener("click", function () {
                            createExchange(match);
                        });

                        card.appendChild(applyButton);

                        container.appendChild(card);
                    });

                } catch (error) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <p>获取推荐失败，请稍后重试。</p>
                        </div>
                    `;

                    console.error("加载匹配推荐失败：", error);
                }
            }

            async function createExchange(match) {
                const confirmed = confirm(
                    "确定向 " + match.username + " 发送交换申请吗？"
                );

                if (!confirmed) {
                    return;
                }

                try {
                    const result = await apiRequest(
                        "/api/exchanges/",
                        "POST",
                        {
                            receiver_id: match.user_id,
                            my_skill: match.my_skill,
                            their_skill: match.their_skill
                        }
                    );

                    showToast(result.message);

                } catch (error) {
                    showToast(error.message);
                }
            }


            let currentExchangeTab = "received";

            async function loadExchanges() {
                const container = document.getElementById("exchangesContainer");

                if (!container) {
                    return;
                }

                container.innerHTML = `
                    <div class="exchange-panel">
                        <p>正在加载交换申请...</p>
                    </div>
                `;

                try {
                    const result = await apiRequest("/api/exchanges/");

                    const exchanges = result.exchanges || [];

                    renderExchanges(exchanges);

                } catch (error) {
                    container.innerHTML = `
                        <div class="exchange-panel">
                            <h3>获取交换申请失败</h3>
                            <p>${error.message}</p>
                        </div>
                    `;
                }
            }


            function renderExchanges(exchanges) {
                const container = document.getElementById("exchangesContainer");

                if (!container) {
                    return;
                }

                const filteredExchanges = exchanges.filter(function (exchange) {
                    if (currentExchangeTab === "received") {
                        return !exchange.is_sender;
                    }

                    return exchange.is_sender;
                });

                if (filteredExchanges.length === 0) {
                    container.innerHTML = `
                        <div class="exchange-panel">
                            <div class="empty-icon">🤝</div>
                            <h3>
                                ${currentExchangeTab === "received"
                                    ? "还没有收到交换申请"
                                    : "还没有发出交换申请"}
                            </h3>
                            <p>去技能大厅或推荐页面寻找适合你的交换伙伴吧！</p>
                            <button class="btn btn-primary" id="goHallBtn">
                                浏览技能
                            </button>
                        </div>
                    `;

                    const goHallBtn = document.getElementById("goHallBtn");

                    if (goHallBtn) {
                        goHallBtn.addEventListener("click", function () {
                            switchPage("hall");
                        });
                    }

                    return;
                }

                container.innerHTML = "";

                filteredExchanges.forEach(function (exchange) {
                    const card = document.createElement("div");

                    card.className = "exchange-card";

                    const otherUsername = exchange.is_sender
                        ? exchange.receiver_username
                        : exchange.sender_username;

                    const title = document.createElement("h3");

                    title.textContent = otherUsername;

                    const status = document.createElement("span");

                    status.className = "exchange-status";

                    status.textContent = exchange.status;

                    const skills = document.createElement("div");

                    skills.className = "exchange-skills";

                    const mySkill = document.createElement("p");

                    mySkill.textContent = "我提供：" + exchange.my_skill;

                    const theirSkill = document.createElement("p");

                    theirSkill.textContent = "对方提供：" + exchange.their_skill;

                    card.appendChild(title);
                    card.appendChild(status);
                    card.appendChild(skills);

                    skills.appendChild(mySkill);
                    skills.appendChild(theirSkill);

                    container.appendChild(card);
                });
            }


            document.querySelectorAll(".exchange-tab").forEach(function (button) {
                button.addEventListener("click", function () {
                    currentExchangeTab = button.dataset.exchangeTab;

                    document.querySelectorAll(".exchange-tab").forEach(function (tab) {
                        tab.classList.toggle(
                            "active",
                            tab.dataset.exchangeTab === currentExchangeTab
                        );
                    });

                    loadExchanges();
                });
            });


            async function switchPage(page) {
                currentPage = page;

                // 更新导航栏选中状态
                document.querySelectorAll(".nav-link").forEach(function (button) {
                    button.classList.toggle(
                        "active",
                        button.dataset.page === page
                    );
                });

                // 切换页面内容
                document.querySelectorAll(".page-panel").forEach(function (panel) {
                    panel.classList.remove("active");
                });

                const target = document.getElementById(page + "Page");
                if (target) {
                    target.classList.add("active");
                }

                // 重新从后端获取最新技能数据
                if (page === "hall" || page === "recommend" || page === "profile") {
                    try {
                        await loadSkills();
                    } catch (error) {
                        showToast("数据刷新失败：" + error.message);
                    }
                }

                if (page === "exchanges") {
                    await loadExchanges();
                }

            }



            // 退出登录
            async function logoutUser() {
                try {
                    const result = await apiRequest("/api/auth/logout", "POST");

                    currentUser = null;

                    // 更新导航栏
                    updateNavActions();

                    // 清空个人中心
                    renderProfile();

                    // 清空推荐页面
                    const recommendContainer = document.getElementById("recommendationsContainer");

                    if (recommendContainer) {
                        recommendContainer.innerHTML = `
                            <div class="empty-state">
                                <div class="empty-icon">🔐</div>
                                <h3>登录后查看技能推荐</h3>
                                <p>登录后即可发现适合你的技能交换伙伴。</p>
                            </div>
                        `;
                    }

                    // 清空交换页面
                    const exchangesContainer = document.getElementById("exchangesContainer");

                    if (exchangesContainer) {
                        exchangesContainer.innerHTML = `
                            <div class="exchange-panel">
                                <div class="empty-icon">🤝</div>
                                <h3>登录后查看交换申请</h3>
                                <p>登录后即可管理收到和发出的交换申请。</p>
                            </div>
                        `;
                    }

                    // 重新加载技能列表
                    await loadSkills();

                    showToast(result.message);

                } catch (error) {
                    showToast(error.message);
                }
            }



            function renderProfile() {
                const content = document.getElementById("profileContent");

                if (!currentUser) {
                    content.innerHTML = `
                        <div class="empty-icon">👤</div>
                        <h3>欢迎来到 SkillSwap</h3>
                        <p>登录后即可管理个人资料和发布的技能。</p>
                        <button class="btn btn-primary" id="profileLoginBtn">
                            立即登录
                        </button>
                    `;

                    document.getElementById("profileLoginBtn")
                        .addEventListener("click", function () {
                            setAuthMode("login");
                            openModal("authModal");
                        });
                    return;
                }

                const mySkills = skills.filter(function (skill) {
                    return skill.is_mine;
                });

                content.innerHTML = `
                    <div class="empty-icon">👋</div>
                    <h3>${escapeHTML(currentUser.username)}</h3>
                    <p>${escapeHTML(currentUser.email)}</p>
                    <button class="btn btn-outline" id="logoutBtn">退出登录</button>

                    <div class="profile-skills">
                        <h3>📚 我发布的技能（${mySkills.length}）</h3>
                        ${
                            mySkills.length === 0
                            ? `<p>你还没有发布技能，去技能大厅发布一个吧！</p>`
                            : mySkills.map(function (skill) {
                                return `
                                    <div class="profile-skill-item">
                                        <div>
                                            <strong>${skill.icon} ${escapeHTML(skill.name)}</strong>
                                            <p>${escapeHTML(skill.description)}</p>
                                        </div>
                                        <div class="profile-skill-actions">
                                            <button class="btn btn-outline edit-skill-btn"
                                                data-id="${escapeHTML(skill.id)}">编辑</button>
                                            <button class="btn btn-danger delete-skill-btn"
                                                data-id="${escapeHTML(skill.id)}">删除</button>
                                        </div>
                                    </div>
                                `;
                            }).join("")
                        }
                    </div>
                `;

                document.getElementById("logoutBtn")
                    .addEventListener("click", logoutUser);

                document.querySelectorAll(".edit-skill-btn").forEach(function (button) {
                    button.addEventListener("click", function () {
                        editSkill(button.dataset.id);
                    });
                });

            document.querySelectorAll(".delete-skill-btn").forEach(function (button) {
                button.addEventListener("click", function () {
                    deleteSkill(button.dataset.id);
                });
            });
            }


            
            function editSkill(skillId) {
                const skill = skills.find(function (item) {
                    return String(item.id) === String(skillId);
                });

                if (!skill) {
                    showToast("没有找到该技能");
                    return;
                }

                editingSkillId = skill.id;

                document.getElementById("publishModalTitle").textContent = "编辑我的技能";
                document.getElementById("publishSubmitText").textContent = "保存修改";

                document.getElementById("skillName").value = skill.name;
                document.getElementById("skillCategory").value = skill.category;
                document.getElementById("skillDescription").value = skill.description;
                document.getElementById("wantedSkill").value = skill.wanted;

                openModal("publishModal");
            }

            async function deleteSkill(skillId) {
                const confirmed = confirm("确定要删除这个技能吗？此操作无法撤销。");

                if (!confirmed) {
                    return;
                }

                try {
                    const result = await apiRequest(
                        "/api/skills/" + encodeURIComponent(skillId),
                        "DELETE"
                    );

                    await loadSkills();

                    showToast(result.message);

                } catch (error) {
                    showToast(error.message);
                }
            }

            function updateNavActions() {
                const actions = document.getElementById("navActions");

                if (!currentUser) {
                    actions.innerHTML = `
                        <button class="btn btn-outline" id="loginBtn">登录</button>
                        <button class="btn btn-primary" id="registerBtn">注册</button>
                    `;

                    document.getElementById("loginBtn").addEventListener("click", function () {
                        setAuthMode("login");
                        openModal("authModal");
                    });

                    document.getElementById("registerBtn").addEventListener("click", function () {
                        setAuthMode("register");
                        openModal("authModal");
                    });

                } else {
                    actions.innerHTML = `
                        <span class="user-name">👤 ${escapeHTML(currentUser.username)}</span>
                        <button class="btn btn-outline" id="logoutBtn">退出</button>
                    `;

                    document.getElementById("logoutBtn").addEventListener("click", logoutUser);
                }
            }

            function setAuthMode(mode) {
                authMode = mode;

                const isRegister = mode === "register";

                document.getElementById("authTitle").textContent =
                    isRegister ? "创建 SkillSwap 账户" : "欢迎回来";

                document.getElementById("authSubmit").textContent =
                    isRegister ? "注册" : "登录";

                document.getElementById("usernameGroup").style.display =
                    isRegister ? "block" : "none";

                document.getElementById("authUsername").required = isRegister;

                document.getElementById("authSwitch").textContent =
                    isRegister ? "已有账户？立即登录" : "还没有账户？立即注册";
            }

            function showSkillDetail(id) {
                const skill = skills.find(function (item) {
                    return String(item.id) === String(id);
                });

                if (!skill) return;

                currentSkill = skill;

                document.getElementById("detailContent").innerHTML = `
                    <div class="detail-icon">${skill.icon}</div>
                    <span class="skill-category">${escapeHTML(skill.category)}</span>
                    <h2 style="margin-top:15px;">${escapeHTML(skill.name)}</h2>
                    <p class="detail-description">${escapeHTML(skill.description)}</p>
                    <p style="font-size:13px; margin-bottom:10px;">
                        分享者：${escapeHTML(skill.person)}
                    </p>
                    <p style="font-size:13px; margin-bottom:10px;">
                        所在地：${escapeHTML(skill.location)}
                    </p>
                    <p style="font-size:13px; margin-bottom:20px;">
                        希望交换：${escapeHTML(skill.wanted)}
                    </p>
                `;

                openModal("detailModal");
            }

            // 导航切换
            document.querySelectorAll(".nav-link").forEach(function (button) {
                button.addEventListener("click", function () {
                    switchPage(button.dataset.page);
                });
            });

            document.getElementById("authSwitch").addEventListener("click", function () {
                setAuthMode(authMode === "login" ? "register" : "login");
            });

            // 登录和注册表单提交
            document.getElementById("authForm").addEventListener("submit", async function (event) {
                event.preventDefault();

                const email = document.getElementById("authEmail").value.trim();
                const password = document.getElementById("authPassword").value;
                const username = document.getElementById("authUsername").value.trim();
                const submitButton = document.getElementById("authSubmit");

                if (authMode === "register" && !username) {
                    showToast("请输入用户名");
                    return;
                }

                const originalText = submitButton.textContent;
                submitButton.disabled = true;
                submitButton.textContent = "请稍候...";

                try {
                    let result;

                    if (authMode === "register") {
                        result = await apiRequest("/api/auth/register", "POST", {
                            username: username,
                            email: email,
                            password: password
                        });
                    } else {
                        result = await apiRequest("/api/auth/login", "POST", {
                            email: email,
                            password: password
                        });
                    }

                    currentUser = result.user;

                    updateNavActions();

                    // 重新获取当前账号对应的技能数据
                    await loadSkills();

                    closeModal("authModal");
                    document.getElementById("authForm").reset();

                    showToast(result.message);

                } catch (error) {
                    showToast(error.message);

                } finally {
                    submitButton.disabled = false;
                    submitButton.textContent = originalText;
                }
            });

            // 发布技能
            document.getElementById("publishBtn").addEventListener("click", function () {
                if (!currentUser) {
                    showToast("请先登录，再发布技能");
                    setAuthMode("login");
                    openModal("authModal");
                    return;
                }

                openModal("publishModal");
            });

            // 发布技能
            document.getElementById("publishForm").addEventListener("submit", async function (event) {
                event.preventDefault();

                const name = document.getElementById("skillName").value.trim();
                const category = document.getElementById("skillCategory").value;
                const description = document.getElementById("skillDescription").value.trim();
                const wanted = document.getElementById("wantedSkill").value.trim();

                const submitButton = event.currentTarget.querySelector('button[type="submit"]');
                const originalText = document.getElementById("publishSubmitText").textContent;

                submitButton.disabled = true;
                document.getElementById("publishSubmitText").textContent = "正在保存...";

                try {
                    let result;

                    if (editingSkillId) {
                        result = await apiRequest(
                            "/api/skills/" + editingSkillId,
                            "PUT",
                            {
                                name: name,
                                category: category,
                                description: description,
                                wanted: wanted
                            }
                        );
                    } else {
                        result = await apiRequest(
                            "/api/skills/",
                            "POST",
                            {
                                name: name,
                                category: category,
                                description: description,
                                wanted: wanted
                            }
                        );
                    }

                    editingSkillId = null;

                    await loadSkills();

                    document.getElementById("publishForm").reset();
                    document.getElementById("publishModalTitle").textContent = "发布我的技能";
                    document.getElementById("publishSubmitText").textContent = "发布技能";

                    closeModal("publishModal");
                    showToast(result.message);

                } catch (error) {
                    showToast(error.message);

                } finally {
                    submitButton.disabled = false;

                    if (editingSkillId) {
                        document.getElementById("publishSubmitText").textContent = "保存修改";
                    } else {
                        document.getElementById("publishSubmitText").textContent = "发布技能";
                    }
                }
            });


            // 搜索
            searchInput.addEventListener("input", renderSkills);

            // 分类筛选
            document.querySelectorAll(".filter-btn").forEach(function (button) {
                button.addEventListener("click", function () {
                    document.querySelectorAll(".filter-btn").forEach(function (item) {
                        item.classList.remove("active");
                    });

                    button.classList.add("active");
                    currentCategory = button.dataset.category;
                    renderSkills();
                });
            });

            // 技能卡片点击
            document.addEventListener("click", function (event) {
                const card = event.target.closest(".skill-card");

                if (card) {
                    showSkillDetail(card.dataset.id);
                }
            });

            // 申请交换
            document.getElementById("requestExchangeBtn").addEventListener("click", function () {
                if (!currentUser) {
                    closeModal("detailModal");
                    setAuthMode("login");
                    openModal("authModal");
                    showToast("请先登录，再申请交换");
                    return;
                }

                closeModal("detailModal");
                showToast("交换申请功能将在后续版本接入");
            });

            // 关闭弹窗
            document.querySelectorAll("[data-close]").forEach(function (button) {
                button.addEventListener("click", function () {
                    closeModal(button.dataset.close);
                });
            });

            // 点击遮罩层关闭
            document.querySelectorAll(".modal-overlay").forEach(function (overlay) {
                overlay.addEventListener("click", function (event) {
                    if (event.target === overlay) {
                        overlay.classList.remove("show");
                    }
                });
            });

            // 其他导航按钮

            // 探索技能按钮
            document.getElementById("exploreBtn").addEventListener("click", function () {
                switchPage("hall");
                window.scrollTo({
                    top: 0,
                    behavior: "smooth"
                });
            });

            // ESC 关闭弹窗
            document.addEventListener("keydown", function (event) {
                if (event.key === "Escape") {
                    document.querySelectorAll(".modal-overlay.show").forEach(function (modal) {
                        modal.classList.remove("show");
                    });
                }
            });



            // 页面初始化
            async function checkLoginStatus() {
                try {
                    const result = await apiRequest("/api/auth/me");

                    currentUser = result.user;

                } catch (error) {
                    currentUser = null;
                }

                // 根据当前登录状态更新导航栏
                updateNavActions();

                // 获取技能数据并更新页面
                try {
                    await loadSkills();
                } catch (error) {
                    showToast("技能加载失败：" + error.message);
                }

                // 更新个人中心
                renderProfile();
            }

            // 首次加载时先检查登录状态
            checkLoginStatus();

        });