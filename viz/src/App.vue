<template>
  <div class="app">
    <div class="sort-controls">
      <button :class="{ active: sortMode === 'alpha' }" @click="setSortMode('alpha')">A-Z</button>
      <button :class="{ active: sortMode === 'first' }" @click="setSortMode('first')">First</button>
      <button :class="{ active: sortMode === 'count' }" @click="setSortMode('count')">Count</button>
    </div>
    <canvas ref="canvas" @wheel="handleWheel" @mousedown="handleMouseDown" @mousemove="handleMouseMove" @mouseup="handleMouseUp" @mouseleave="handleMouseUp" @click="handleClick"></canvas>
    <div v-if="tooltip.visible" class="tooltip" :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }">
      <div v-if="tooltip.isCluster">
        <strong>{{ tooltip.count }} emails</strong><br>
        {{ tooltip.dateRange }}<br>
        <small>Click to zoom in</small>
      </div>
      <div v-else>
        <strong>{{ tooltip.date }}</strong><br>
        From: {{ tooltip.sender }}<br>
        To: {{ tooltip.receiver }}<br>
        Type: {{ tooltip.messageType }}<br>
        <span v-if="tooltip.subject">Subject: {{ tooltip.subject }}<br></span>
        <small>{{ tooltip.summary }}</small>
      </div>
    </div>
    <div v-if="nameTooltip.visible" class="name-tooltip" :style="{ left: nameTooltip.x + 'px', top: nameTooltip.y + 'px' }">
      {{ nameTooltip.name }}
    </div>

    <!-- Help Modal -->
    <div v-if="showHelpModal" class="modal-overlay" @click="showHelpModal = false">
      <div class="modal" @click.stop>
        <h2>Email Timeline Visualization</h2>

        <div class="modal-section">
          <h3>Navigation</h3>
          <p class="modal-hint">Works like Google Maps</p>
          <p><strong>Pan:</strong> Click and drag in empty space to move around</p>
          <p><strong>Zoom:</strong> Use mouse wheel to zoom in/out</p>
        </div>

        <div class="modal-section">
          <h3>Node Colors (Message Type)</h3>
          <div class="legend-row">
            <span class="legend-dot" style="background: #4ecdc4;"></span>
            <span>Original message</span>
          </div>
          <div class="legend-row">
            <span class="legend-dot" style="background: #ff6b6b;"></span>
            <span>Reply</span>
          </div>
          <div class="legend-row">
            <span class="legend-dot" style="background: #ffe66d;"></span>
            <span>Forward</span>
          </div>
        </div>

        <div class="modal-section">
          <h3>Arrow Direction</h3>
          <div class="legend-row">
            <span class="arrow-example">&#9650;</span>
            <span>Sent by Jeffrey Epstein</span>
          </div>
          <div class="legend-row">
            <span class="arrow-example">&#9660;</span>
            <span>Received by Jeffrey Epstein</span>
          </div>
          <div class="legend-row">
            <span class="arrow-example-double">&#9650;<br>&#9660;</span>
            <span>Mix of sent and received (in clusters)</span>
          </div>
        </div>

        <div class="modal-section">
          <h3>Sorting</h3>
          <p>Use the buttons at the top left to sort names:</p>
          <p><strong>A-Z:</strong> Alphabetical &nbsp; <strong>First:</strong> By earliest email &nbsp; <strong>Count:</strong> By email volume</p>
        </div>

        <div class="modal-section">
          <h3>Interactions</h3>
          <p><strong>Hover</strong> over a node to see email metadata and summary</p>
          <p><strong>Click</strong> on a single email to open the original document</p>
          <p><strong>Click</strong> on a cluster to zoom in (may need multiple clicks)</p>
          <p><strong>Click</strong> on a name to Google search that person</p>
        </div>

        <div class="modal-warning">
          <strong>Note:</strong> Data was extracted automatically. Please verify information against the original source documents.
        </div>

        <button class="modal-close" @click="showHelpModal = false">Okay</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      canvas: null,
      ctx: null,
      data: null,
      contacts: [],
      allEmails: [],

      // Timeline bounds
      minTimestamp: null,
      maxTimestamp: null,

      // View state
      viewX: 0,
      viewY: 0,
      zoom: 1,
      minZoom: 0.0000001,
      maxZoom: 1,

      // Interaction
      isDragging: false,
      lastMouseX: 0,
      lastMouseY: 0,

      // Layout constants
      rowHeight: 26,
      nameColumnWidth: 180,
      timelineHeight: 50,

      // Primary person email variations
      primaryEmails: [
        'jeevacation@gmail.com',
        'e:jeeitunes@gmail.com',
        'jeeitunes@gmail.com',
        'jeffrey e.',
        'jeffreye.'
      ],

      // Colors
      colors: {
        background: '#1a1a2e',
        text: '#e0e0e0',
        textMuted: '#aaa',
        gridLine: '#555',
        rowHover: 'rgba(255,255,255,0.08)',
        original: '#4ecdc4',
        reply: '#ff6b6b',
        forward: '#ffe66d',
        sent: '#45b7d1',
        received: '#f39c12'
      },

      // Tooltip
      tooltip: {
        visible: false,
        x: 0,
        y: 0,
        isCluster: false,
        count: 0,
        dateRange: '',
        date: '',
        sender: '',
        receiver: '',
        messageType: '',
        subject: '',
        summary: ''
      },

      hoveredRow: -1,
      hoveredNode: null,

      // Name tooltip for truncated names
      nameTooltip: {
        visible: false,
        x: 0,
        y: 0,
        name: ''
      },

      // Cached nodes for performance
      cachedNodes: [],
      cacheKey: '',

      // Visual style: 'solid' or 'heatmap'
      nodeStyle: 'solid',

      // Help modal
      showHelpModal: true,

      // Sort mode: 'alpha', 'first', 'count'
      sortMode: 'alpha'
    }
  },

  async mounted() {
    this.canvas = this.$refs.canvas
    this.ctx = this.canvas.getContext('2d')

    window.addEventListener('resize', this.resize)
    this.resize()

    await this.loadData()
    this.initializeView()
    this.render()
  },

  beforeUnmount() {
    window.removeEventListener('resize', this.resize)
  },

  methods: {
    resize() {
      this.canvas.width = window.innerWidth
      this.canvas.height = window.innerHeight
      this.render()
    },

    async loadData() {
      const response = await fetch('/data/all_emails.json')
      this.data = await response.json()

      // Process contacts
      this.allContacts = Object.keys(this.data)
      this.sortContacts()

      // Flatten all emails with contact reference
      this.allEmails = []
      let minTs = Infinity
      let maxTs = -Infinity

      for (const contact of this.contacts) {
        const contactData = this.data[contact]
        for (const email of contactData.emails) {
          if (email.timestamp) {
            this.allEmails.push({
              ...email,
              contact,
              isSent: this.isPrimaryPerson(email.senderEmail || email.sender)
            })
            minTs = Math.min(minTs, email.timestamp)
            maxTs = Math.max(maxTs, email.timestamp)
          }
        }
      }

      this.minTimestamp = minTs
      this.maxTimestamp = maxTs

      // Pre-process contact data for faster access
      this.contactEmailData = {}
      const contactsWithEmails = []

      for (const contact of this.allContacts) {
        const allEmails = this.data[contact].emails
          .filter(e => e.timestamp) // Only include emails with valid timestamps

        // Filter emails based on contact:
        // - If contact is Jeffrey Epstein: only show emails to/from himself
        // - Otherwise: show all emails (these represent correspondence with that contact)
        const isJeffreyEpstein = contact === 'Jeffrey Epstein'
        const emails = allEmails
          .filter(e => {
            if (!isJeffreyEpstein) return true
            // For Jeffrey Epstein row, only show self-emails
            const senderIsJE = this.isPrimaryPerson(e.senderEmail || e.sender)
            const receiverIsJE = this.isPrimaryPerson(e.receiverEmail || e.receiver)
            return senderIsJE && receiverIsJE
          })
          .map(e => ({
            ...e,
            isSent: this.isPrimaryPerson(e.senderEmail || e.sender)
          }))
          .sort((a, b) => a.timestamp - b.timestamp)

        // Only include contacts that have at least one email with a timestamp
        if (emails.length > 0) {
          this.contactEmailData[contact] = {
            emails,
            minTs: emails[0].timestamp,
            maxTs: emails[emails.length - 1].timestamp
          }
          contactsWithEmails.push(contact)
        }
      }

      // Update allContacts to only include contacts with valid emails
      this.allContacts = contactsWithEmails

      // Re-sort now that contactEmailData is available
      this.sortContacts()
    },

    isPrimaryPerson(email) {
      if (!email || typeof email !== 'string') return false
      const lower = email.toLowerCase()
      return this.primaryEmails.some(pe => lower.includes(pe.toLowerCase()))
    },

    setSortMode(mode) {
      if (this.sortMode !== mode) {
        this.sortMode = mode
        this.sortContacts()
        this.cacheKey = '' // Invalidate cache
        // Jump to top for First and Count sorts
        if (mode === 'first' || mode === 'count') {
          this.viewY = 0
        }
        this.render()
      }
    },

    sortContacts() {
      if (this.sortMode === 'alpha') {
        this.contacts = [...this.allContacts].sort((a, b) =>
          a.toLowerCase().localeCompare(b.toLowerCase())
        )
      } else if (this.sortMode === 'first') {
        // Sort by first email date ascending
        this.contacts = [...this.allContacts].sort((a, b) => {
          const aData = this.contactEmailData?.[a]
          const bData = this.contactEmailData?.[b]
          const aMin = aData?.minTs ?? Infinity
          const bMin = bData?.minTs ?? Infinity
          return aMin - bMin
        })
      } else if (this.sortMode === 'count') {
        // Sort by email count descending
        this.contacts = [...this.allContacts].sort((a, b) => {
          const aCount = this.data[a]?.emails?.length ?? 0
          const bCount = this.data[b]?.emails?.length ?? 0
          return bCount - aCount
        })
      }
    },

    initializeView() {
      // Start at middle zoom and centered
      const timeRange = this.maxTimestamp - this.minTimestamp
      const contentWidth = this.canvas.width - this.nameColumnWidth

      // Set zoom limits based on data
      // Min zoom: entire timeline fits in ~50px
      this.minZoom = 50 / timeRange
      // Max zoom: 1 hour spans the content width
      this.maxZoom = contentWidth / 3600

      // Set zoom so entire timeline fits initially, with some padding
      this.zoom = contentWidth / timeRange * 0.8

      // viewX represents scroll position: 0 means minTimestamp is at left edge
      // Center the timeline
      this.viewX = (timeRange * this.zoom - contentWidth) / 2

      // Center vertically
      const totalHeight = this.contacts.length * this.rowHeight
      this.viewY = Math.max(0, (totalHeight - this.canvas.height + this.timelineHeight) / 2)

    },

    // Convert viewX to timestamp
    viewXToTimestamp(pixelX) {
      return this.minTimestamp + (this.viewX + pixelX) / this.zoom
    },

    // Convert timestamp to screen X
    timestampToScreenX(timestamp) {
      return this.nameColumnWidth + (timestamp - this.minTimestamp) * this.zoom - this.viewX
    },

    handleWheel(e) {
      e.preventDefault()

      const rect = this.canvas.getBoundingClientRect()
      const mouseX = e.clientX - rect.left - this.nameColumnWidth

      // Get timestamp at mouse position before zoom
      const timestampAtMouse = this.viewXToTimestamp(mouseX)

      // Zoom - increase factor at higher zoom levels for faster zooming
      const zoomRatio = (this.zoom - this.minZoom) / (this.maxZoom - this.minZoom)
      const baseFactor = e.deltaY > 0 ? 0.9 : 1.1
      // At low zoom: 0.9/1.1, at high zoom: 0.5/2.0
      const zoomFactor = e.deltaY > 0
        ? baseFactor - (zoomRatio * 0.4)  // 0.9 -> 0.5
        : baseFactor + (zoomRatio * 0.9)  // 1.1 -> 2.0
      const newZoom = Math.max(this.minZoom, Math.min(this.maxZoom, this.zoom * zoomFactor))

      // Adjust viewX to keep timestamp at mouse position
      this.viewX = (timestampAtMouse - this.minTimestamp) * newZoom - mouseX
      this.zoom = newZoom

      this.scheduleRender()
    },

    handleMouseDown(e) {
      this.isDragging = true
      this.lastMouseX = e.clientX
      this.lastMouseY = e.clientY
      this.canvas.style.cursor = 'grabbing'
    },

    handleMouseMove(e) {
      const rect = this.canvas.getBoundingClientRect()
      const mouseX = e.clientX - rect.left
      const mouseY = e.clientY - rect.top

      if (this.isDragging) {
        const dx = e.clientX - this.lastMouseX
        const dy = e.clientY - this.lastMouseY

        this.viewX -= dx
        this.viewY -= dy

        this.lastMouseX = e.clientX
        this.lastMouseY = e.clientY

        this.scheduleRender()
      } else {
        // Check hover
        this.checkHover(mouseX, mouseY)
      }
    },

    scheduleRender() {
      if (!this.renderScheduled) {
        this.renderScheduled = true
        requestAnimationFrame(() => {
          this.renderScheduled = false
          this.render()
        })
      }
    },

    handleMouseUp() {
      this.isDragging = false
      this.canvas.style.cursor = 'default'
    },

    handleClick(e) {
      const rect = this.canvas.getBoundingClientRect()
      const mouseX = e.clientX - rect.left
      const mouseY = e.clientY - rect.top

      // Check if clicking on name column
      if (mouseX < this.nameColumnWidth && mouseY > this.timelineHeight) {
        const rowIndex = Math.floor((mouseY - this.timelineHeight + this.viewY) / this.rowHeight)
        if (rowIndex >= 0 && rowIndex < this.contacts.length) {
          const contactName = this.contacts[rowIndex]
          // Open Google search in new tab
          const searchQuery = encodeURIComponent(contactName)
          window.open(`https://www.google.com/search?q=${searchQuery}`, '_blank')
          return
        }
      }

      if (this.hoveredNode) {
        if (this.hoveredNode.isCluster) {
          // Zoom into cluster
          const node = this.hoveredNode
          const centerTimestamp = (node.minTimestamp + node.maxTimestamp) / 2

          // Calculate zoom to spread cluster across ~200px
          const timeRange = node.maxTimestamp - node.minTimestamp
          if (timeRange > 0) {
            const targetZoom = 200 / timeRange
            this.zoom = Math.min(this.maxZoom, targetZoom)
          } else {
            this.zoom = Math.min(this.maxZoom, this.zoom * 5)
          }

          // Center on cluster
          const contentWidth = this.canvas.width - this.nameColumnWidth
          this.viewX = (centerTimestamp - this.minTimestamp) * this.zoom - contentWidth / 2

          this.render()
        } else {
          // Single email - open Dropbox preview
          const email = this.hoveredNode.emails[0]
          if (email.dropbox_url) {
            window.open(email.dropbox_url, '_blank')
          }
        }
      }
    },

    buildDropboxUrl(sourceFile) {
      // source_file format: "002_HOUSE_OVERSIGHT_012477.jpg.json"
      // Extract prefix (e.g., "002") and filename (e.g., "HOUSE_OVERSIGHT_012477.jpg")
      const match = sourceFile.match(/^(\d+)_(.+)\.json$/)
      if (match) {
        const prefix = match[1]
        const filename = match[2]
        return `https://www.dropbox.com/scl/fo/9bq6uj0pnycpa4gxqiuzs/ANovXi2UNNBhXvHKrvavrrE/IMAGES/${prefix}?dl=0&preview=${filename}&rlkey=3s6ggcjihou9nt8srsn2qt1n7`
      }
      return null
    },

    checkHover(mouseX, mouseY) {
      // Check which row
      const rowIndex = Math.floor((mouseY - this.timelineHeight + this.viewY) / this.rowHeight)
      const newHoveredRow = rowIndex >= 0 && rowIndex < this.contacts.length ? rowIndex : -1

      // Check if hovering over name column
      this.nameTooltip.visible = false
      if (mouseX < this.nameColumnWidth && mouseY > this.timelineHeight && newHoveredRow >= 0) {
        this.canvas.style.cursor = 'pointer'
        // Show name tooltip if name is truncated
        const contactName = this.contacts[newHoveredRow]
        if (contactName.length > 22) {
          this.nameTooltip.visible = true
          this.nameTooltip.name = contactName
          this.nameTooltip.x = mouseX + 10
          this.nameTooltip.y = mouseY - 10
        }
      } else if (!this.isDragging) {
        this.canvas.style.cursor = 'grab'
      }

      // Check nodes
      let newHoveredNode = null
      this.tooltip.visible = false

      if (mouseX > this.nameColumnWidth && mouseY > this.timelineHeight) {
        const nodes = this.cachedNodes.length > 0 ? this.cachedNodes : this.getVisibleNodes()
        for (const node of nodes) {
          const dx = mouseX - node.x
          const dy = mouseY - node.y
          const dist = Math.sqrt(dx * dx + dy * dy)

          if (dist < node.radius + 3) {
            newHoveredNode = node
            this.showTooltip(node, mouseX, mouseY)
            break
          }
        }
      }

      // Only re-render if hover state changed
      if (newHoveredRow !== this.hoveredRow || newHoveredNode !== this.hoveredNode) {
        this.hoveredRow = newHoveredRow
        this.hoveredNode = newHoveredNode
        this.render()
      }
    },

    showTooltip(node, x, y) {
      this.tooltip.visible = true
      this.tooltip.x = x + 10
      this.tooltip.y = y + 10

      if (node.isCluster) {
        this.tooltip.isCluster = true
        this.tooltip.count = node.emails.length
        const minDate = new Date(node.minTimestamp * 1000).toLocaleDateString()
        const maxDate = new Date(node.maxTimestamp * 1000).toLocaleDateString()
        this.tooltip.dateRange = `${minDate} - ${maxDate}`
      } else {
        this.tooltip.isCluster = false
        const email = node.emails[0]
        this.tooltip.date = new Date(email.timestamp * 1000).toLocaleString()

        // Handle arrays for sender/receiver
        const sender = email.sender || email.senderEmail || 'Unknown'
        const receiver = email.receiver || email.receiverEmail || 'Unknown'
        this.tooltip.sender = Array.isArray(sender) ? sender.join(', ') : sender
        this.tooltip.receiver = Array.isArray(receiver) ? receiver.join(', ') : receiver

        this.tooltip.messageType = email.messageType || 'Unknown'
        this.tooltip.subject = email.subject || ''
        this.tooltip.summary = email.summary || ''
      }
    },

    getVisibleNodes() {
      const contentWidth = this.canvas.width - this.nameColumnWidth
      const screenHeight = this.canvas.height

      // Get visible time range
      const minVisibleTs = this.viewXToTimestamp(0)
      const maxVisibleTs = this.viewXToTimestamp(contentWidth)

      // Get visible row range
      const minRow = Math.floor(this.viewY / this.rowHeight)
      const maxRow = Math.ceil((this.viewY + screenHeight - this.timelineHeight) / this.rowHeight)

      // Check cache with rounded values to improve hit rate
      const cacheKey = `${Math.floor(minVisibleTs)}-${Math.ceil(maxVisibleTs)}-${minRow}-${maxRow}-${this.zoom.toFixed(8)}`
      if (this.cacheKey === cacheKey) {
        return this.cachedNodes
      }

      const nodes = []
      // Dynamic cluster threshold - reduce as zoom increases
      // At min zoom: 10px, at max zoom: keep small threshold to group emails for staggering
      const zoomRatio = (this.zoom - this.minZoom) / (this.maxZoom - this.minZoom)
      const clusterThreshold = zoomRatio >= 0.5 ? 20 : 10 * (1 - zoomRatio)
      const actualMinRow = Math.max(0, minRow)
      const actualMaxRow = Math.min(this.contacts.length, maxRow)

      for (let i = actualMinRow; i < actualMaxRow; i++) {
        const contact = this.contacts[i]
        const contactData = this.contactEmailData[contact]
        if (!contactData) continue

        // Quick bounds check
        if (contactData.maxTs < minVisibleTs || contactData.minTs > maxVisibleTs) continue

        // Binary search for start index
        const emails = contactData.emails
        const emailCount = emails.length

        // Find first email >= minVisibleTs
        let lo = 0, hi = emailCount
        while (lo < hi) {
          const mid = (lo + hi) >> 1
          if (emails[mid].timestamp < minVisibleTs) lo = mid + 1
          else hi = mid
        }
        const startIdx = lo

        // Find first email > maxVisibleTs
        lo = startIdx
        hi = emailCount
        while (lo < hi) {
          const mid = (lo + hi) >> 1
          if (emails[mid].timestamp <= maxVisibleTs) lo = mid + 1
          else hi = mid
        }
        const endIdx = lo

        if (startIdx >= endIdx) continue

        // Calculate y once per row
        const y = this.timelineHeight + (i + 0.5) * this.rowHeight - this.viewY

        // Skip entire row if y is off-screen
        if (y < this.timelineHeight - 20 || y > screenHeight + 20) continue

        // For small number of emails, skip clustering overhead
        if (endIdx - startIdx === 1) {
          const email = emails[startIdx]
          const x = this.timestampToScreenX(email.timestamp)
          if (x >= this.nameColumnWidth - 10 && x <= this.canvas.width + 10) {
            nodes.push({
              x,
              y,
              radius: 10,
              emails: [email],
              isCluster: false,
              hasSent: email.isSent,
              hasReceived: !email.isSent,
              dominantType: email.messageType || 'Original',
              minTimestamp: email.timestamp,
              maxTimestamp: email.timestamp,
              contactIndex: i
            })
          }
          continue
        }

        // Cluster emails
        const clusters = []
        let currentCluster = [emails[startIdx]]
        let prevX = (emails[startIdx].timestamp - this.minTimestamp) * this.zoom

        for (let j = startIdx + 1; j < endIdx; j++) {
          const currX = (emails[j].timestamp - this.minTimestamp) * this.zoom

          if (currX - prevX < clusterThreshold) {
            currentCluster.push(emails[j])
          } else {
            clusters.push(currentCluster)
            currentCluster = [emails[j]]
          }
          prevX = currX
        }
        clusters.push(currentCluster)

        // Create nodes from clusters
        for (let c = 0; c < clusters.length; c++) {
          const cluster = clusters[c]
          const clusterLen = cluster.length
          const minTs = cluster[0].timestamp
          const maxTs = cluster[clusterLen - 1].timestamp

          const x = this.timestampToScreenX((minTs + maxTs) / 2)

          // Skip if off-screen
          const radius = Math.min(20, 8 + Math.sqrt(clusterLen) * 2)
          if (x < this.nameColumnWidth - radius || x > this.canvas.width + radius) continue

          let hasSent = false, hasReceived = false
          let origCount = 0, replyCount = 0, fwdCount = 0

          for (let k = 0; k < clusterLen; k++) {
            const e = cluster[k]
            if (e.isSent) hasSent = true
            else hasReceived = true
            const mt = e.messageType
            if (mt === 'Reply') replyCount++
            else if (mt === 'Forward') fwdCount++
            else origCount++
          }

          let dominantType = 'Original'
          if (replyCount > origCount && replyCount >= fwdCount) dominantType = 'Reply'
          else if (fwdCount > origCount && fwdCount > replyCount) dominantType = 'Forward'

          // At high zoom, stagger overlapping emails within cluster
          if (zoomRatio >= 0.5 && clusterLen > 1) {
            // Create individual staggered nodes
            for (let k = 0; k < clusterLen; k++) {
              const e = cluster[k]
              const emailX = this.timestampToScreenX(e.timestamp)
              // Stagger vertically: spread above/below center with more spacing
              const staggerOffset = (k - (clusterLen - 1) / 2) * 14
              const staggerY = y + staggerOffset

              nodes.push({
                x: emailX,
                y: staggerY,
                radius: 8,
                emails: [e],
                isCluster: false,
                hasSent: e.isSent,
                hasReceived: !e.isSent,
                dominantType: e.messageType || 'Original',
                minTimestamp: e.timestamp,
                maxTimestamp: e.timestamp,
                contactIndex: i
              })
            }
          } else {
            nodes.push({
              x,
              y,
              radius,
              emails: cluster,
              isCluster: clusterLen > 1,
              hasSent,
              hasReceived,
              dominantType,
              minTimestamp: minTs,
              maxTimestamp: maxTs,
              contactIndex: i
            })
          }
        }
      }

      this.cachedNodes = nodes
      this.cacheKey = cacheKey
      return nodes
    },

    render() {
      if (!this.ctx || !this.data) return

      const ctx = this.ctx
      const width = this.canvas.width
      const height = this.canvas.height

      // Clear
      ctx.fillStyle = this.colors.background
      ctx.fillRect(0, 0, width, height)

      // Draw rows
      this.drawRows()

      // Draw nodes
      const nodes = this.getVisibleNodes()
      this.drawNodes(nodes)

      // Draw timeline (on top)
      this.drawTimeline()

      // Draw name column (on top)
      this.drawNameColumn()
    },

    drawRows() {
      const ctx = this.ctx
      const contentWidth = this.canvas.width - this.nameColumnWidth
      const canvasWidth = this.canvas.width
      const screenHeight = this.canvas.height

      const minRow = Math.floor(this.viewY / this.rowHeight)
      const maxRow = Math.ceil((this.viewY + screenHeight - this.timelineHeight) / this.rowHeight)
      const actualMinRow = Math.max(0, minRow)
      const actualMaxRow = Math.min(this.contacts.length, maxRow)

      // Batch the dashed lines
      ctx.strokeStyle = this.colors.gridLine
      ctx.setLineDash([2, 4])

      for (let i = actualMinRow; i < actualMaxRow; i++) {
        const y = this.timelineHeight + (i + 0.5) * this.rowHeight - this.viewY

        // Skip if completely off-screen
        if (y < this.timelineHeight - 10 || y > screenHeight + 10) continue

        // Row hover highlight
        if (i === this.hoveredRow) {
          ctx.fillStyle = this.colors.rowHover
          ctx.fillRect(this.nameColumnWidth, y - this.rowHeight / 2, contentWidth, this.rowHeight)
        }

        // Get contact's email range
        const contact = this.contacts[i]
        const contactData = this.contactEmailData[contact]
        if (!contactData) continue

        // Draw dashed line
        const startX = this.timestampToScreenX(contactData.minTs)
        const endX = this.timestampToScreenX(contactData.maxTs)

        // Skip if line is completely off-screen
        if (endX < this.nameColumnWidth || startX > canvasWidth) continue

        ctx.beginPath()
        ctx.moveTo(Math.max(this.nameColumnWidth, startX), y)
        ctx.lineTo(Math.min(canvasWidth, endX), y)
        ctx.stroke()
      }

      ctx.setLineDash([])
    },

    drawNodes(nodes) {
      const ctx = this.ctx

      for (const node of nodes) {
        // Get color based on message type
        let color = this.colors.original
        if (node.dominantType === 'Reply') color = this.colors.reply
        else if (node.dominantType === 'Forward') color = this.colors.forward

        if (this.nodeStyle === 'heatmap') {
          // Heatmap style: radial gradient with glow
          const gradient = ctx.createRadialGradient(
            node.x, node.y, 0,
            node.x, node.y, node.radius * 1.5
          )

          // Parse the color to create gradient stops
          const intensity = node.isCluster ? Math.min(1, node.emails.length / 10) : 0.8

          // Bright center, fading to transparent
          gradient.addColorStop(0, color)
          gradient.addColorStop(0.3, this.adjustColorAlpha(color, 0.9 * intensity))
          gradient.addColorStop(0.6, this.adjustColorAlpha(color, 0.5 * intensity))
          gradient.addColorStop(1, this.adjustColorAlpha(color, 0))

          ctx.beginPath()
          ctx.arc(node.x, node.y, node.radius * 1.5, 0, Math.PI * 2)
          ctx.fillStyle = gradient
          ctx.fill()

          // Inner bright core
          const coreGradient = ctx.createRadialGradient(
            node.x, node.y, 0,
            node.x, node.y, node.radius * 0.6
          )
          coreGradient.addColorStop(0, '#ffffff')
          coreGradient.addColorStop(0.5, this.adjustColorAlpha(color, 0.9))
          coreGradient.addColorStop(1, color)

          ctx.beginPath()
          ctx.arc(node.x, node.y, node.radius * 0.6, 0, Math.PI * 2)
          ctx.fillStyle = coreGradient
          ctx.fill()
        } else {
          // Solid style (original)
          ctx.beginPath()
          ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2)
          ctx.fillStyle = color
          ctx.fill()
        }

        // Draw arrow using canvas paths for better visibility
        const arrowSize = node.radius * 0.6
        ctx.strokeStyle = this.nodeStyle === 'heatmap' ? 'rgba(0,0,0,0.7)' : '#000'
        ctx.fillStyle = this.nodeStyle === 'heatmap' ? 'rgba(0,0,0,0.7)' : '#000'
        ctx.lineWidth = 2

        if (node.hasSent && node.hasReceived) {
          // Both directions - draw double arrow
          this.drawArrow(ctx, node.x, node.y - arrowSize * 0.3, arrowSize * 0.8, true)  // up
          this.drawArrow(ctx, node.x, node.y + arrowSize * 0.3, arrowSize * 0.8, false) // down
        } else if (node.hasSent) {
          // Up arrow (sent)
          this.drawArrow(ctx, node.x, node.y, arrowSize, true)
        } else {
          // Down arrow (received)
          this.drawArrow(ctx, node.x, node.y, arrowSize, false)
        }

        // Draw count for clusters
        if (node.isCluster && node.radius > 8) {
          ctx.font = 'bold 10px sans-serif'
          ctx.fillStyle = this.colors.text
          ctx.textAlign = 'center'
          ctx.textBaseline = 'middle'
          ctx.fillText(node.emails.length.toString(), node.x, node.y + node.radius + 10)
        }
      }
    },

    adjustColorAlpha(hexColor, alpha) {
      // Convert hex to rgba
      const r = parseInt(hexColor.slice(1, 3), 16)
      const g = parseInt(hexColor.slice(3, 5), 16)
      const b = parseInt(hexColor.slice(5, 7), 16)
      return `rgba(${r}, ${g}, ${b}, ${alpha})`
    },

    drawArrow(ctx, x, y, size, isUp) {
      ctx.beginPath()
      if (isUp) {
        // Up arrow
        ctx.moveTo(x, y - size * 0.5)
        ctx.lineTo(x - size * 0.4, y + size * 0.2)
        ctx.lineTo(x + size * 0.4, y + size * 0.2)
      } else {
        // Down arrow
        ctx.moveTo(x, y + size * 0.5)
        ctx.lineTo(x - size * 0.4, y - size * 0.2)
        ctx.lineTo(x + size * 0.4, y - size * 0.2)
      }
      ctx.closePath()
      ctx.fill()
    },

    drawTimeline() {
      const ctx = this.ctx
      const width = this.canvas.width

      // Background
      ctx.fillStyle = this.colors.background
      ctx.fillRect(0, 0, width, this.timelineHeight)

      // Determine tick interval based on zoom
      const pixelsPerSecond = this.zoom
      const secondsPerDay = 86400
      const secondsPerWeek = secondsPerDay * 7
      const secondsPerMonth = secondsPerDay * 30
      const secondsPerQuarter = secondsPerDay * 91
      const secondsPerYear = secondsPerDay * 365

      let interval, format, minSpacing
      const pixelsPer = (seconds) => seconds * pixelsPerSecond

      // Use larger spacing thresholds to prevent overlap
      if (pixelsPer(secondsPerYear) < 80) {
        interval = secondsPerYear
        format = 'year'
        minSpacing = 60
      } else if (pixelsPer(secondsPerQuarter) < 80) {
        interval = secondsPerQuarter
        format = 'quarter'
        minSpacing = 80
      } else if (pixelsPer(secondsPerMonth) < 80) {
        interval = secondsPerMonth
        format = 'month'
        minSpacing = 70
      } else if (pixelsPer(secondsPerWeek) < 80) {
        interval = secondsPerWeek
        format = 'week'
        minSpacing = 70
      } else if (pixelsPer(secondsPerDay) < 80) {
        interval = secondsPerDay
        format = 'day'
        minSpacing = 70
      } else {
        interval = 3600
        format = 'hour'
        minSpacing = 80
      }

      // Find first tick
      const startTs = this.viewXToTimestamp(0)
      const firstTick = Math.ceil(startTs / interval) * interval

      ctx.fillStyle = this.colors.text
      ctx.font = '12px sans-serif'
      ctx.textAlign = 'center'

      const endTs = this.viewXToTimestamp(width - this.nameColumnWidth)
      let lastLabelX = -1000

      for (let ts = firstTick; ts < endTs; ts += interval) {
        const x = this.timestampToScreenX(ts)
        if (x < this.nameColumnWidth) continue

        // Skip if too close to last label
        if (x - lastLabelX < minSpacing) continue

        // Tick line
        ctx.strokeStyle = this.colors.gridLine
        ctx.beginPath()
        ctx.moveTo(x, this.timelineHeight - 8)
        ctx.lineTo(x, this.timelineHeight)
        ctx.stroke()

        // Label
        const date = new Date(ts * 1000)
        let label
        switch (format) {
          case 'year':
            label = date.getFullYear().toString()
            break
          case 'quarter':
            label = `Q${Math.floor(date.getMonth() / 3) + 1} ${date.getFullYear()}`
            break
          case 'month':
            label = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
            break
          case 'week':
          case 'day':
            label = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' })
            break
          case 'hour':
            label = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
            break
        }

        ctx.fillText(label, x, this.timelineHeight - 20)
        lastLabelX = x
      }

      // Bottom border
      ctx.strokeStyle = this.colors.gridLine
      ctx.beginPath()
      ctx.moveTo(0, this.timelineHeight)
      ctx.lineTo(width, this.timelineHeight)
      ctx.stroke()
    },

    drawNameColumn() {
      const ctx = this.ctx

      // Background
      ctx.fillStyle = this.colors.background
      ctx.fillRect(0, 0, this.nameColumnWidth, this.canvas.height)

      // Names
      ctx.fillStyle = this.colors.text
      ctx.font = '15px sans-serif'
      ctx.textAlign = 'left'
      ctx.textBaseline = 'middle'

      const minRow = Math.floor(this.viewY / this.rowHeight)
      const maxRow = Math.ceil((this.viewY + this.canvas.height - this.timelineHeight) / this.rowHeight)

      for (let i = Math.max(0, minRow); i < Math.min(this.contacts.length, maxRow); i++) {
        const y = this.timelineHeight + (i + 0.5) * this.rowHeight - this.viewY
        if (y < this.timelineHeight || y > this.canvas.height) continue

        const name = this.contacts[i]
        const displayName = name.length > 22 ? name.substring(0, 20) + '...' : name

        ctx.fillStyle = i === this.hoveredRow ? this.colors.text : this.colors.textMuted
        ctx.fillText(displayName, 8, y)
      }

      // Right border
      ctx.strokeStyle = this.colors.gridLine
      ctx.beginPath()
      ctx.moveTo(this.nameColumnWidth, 0)
      ctx.lineTo(this.nameColumnWidth, this.canvas.height)
      ctx.stroke()

      // Top-left corner
      ctx.fillStyle = this.colors.background
      ctx.fillRect(0, 0, this.nameColumnWidth, this.timelineHeight)
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  overflow: hidden;
  background: #1a1a2e;
}

.app {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

canvas {
  display: block;
  cursor: grab;
}

.sort-controls {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 100;
  display: flex;
  gap: 4px;
}

.sort-controls button {
  padding: 4px 8px;
  font-size: 11px;
  background: #2a2a3e;
  color: #aaa;
  border: 1px solid #444;
  border-radius: 4px;
  cursor: pointer;
}

.sort-controls button:hover {
  background: #3a3a4e;
  color: #fff;
}

.sort-controls button.active {
  background: #4a4a6e;
  color: #fff;
  border-color: #666;
}

.tooltip {
  position: absolute;
  background: rgba(30, 30, 50, 0.95);
  color: #e0e0e0;
  padding: 12px 16px;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.5;
  max-width: 400px;
  pointer-events: none;
  z-index: 1000;
  border: 1px solid #444;
}

.tooltip strong {
  font-size: 16px;
}

.tooltip small {
  color: #bbb;
  display: block;
  margin-top: 6px;
  max-height: 80px;
  overflow: hidden;
  font-size: 13px;
}

.name-tooltip {
  position: absolute;
  background: rgba(30, 30, 50, 0.95);
  color: #e0e0e0;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 14px;
  pointer-events: none;
  z-index: 1000;
  border: 1px solid #444;
  white-space: nowrap;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal {
  background: #1a1a2e;
  border: 1px solid #444;
  border-radius: 12px;
  padding: 24px 32px;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  color: #e0e0e0;
}

.modal h2 {
  margin: 0 0 20px 0;
  color: #fff;
  font-size: 22px;
  text-align: center;
}

.modal-section {
  margin-bottom: 18px;
}

.modal-section h3 {
  margin: 0 0 8px 0;
  color: #4ecdc4;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.modal-section p {
  margin: 4px 0;
  font-size: 14px;
  line-height: 1.5;
}

.legend-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 6px 0;
  font-size: 14px;
}

.legend-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  flex-shrink: 0;
}

.arrow-example {
  width: 16px;
  text-align: center;
  font-size: 14px;
  color: #fff;
}

.arrow-example-double {
  width: 16px;
  text-align: center;
  font-size: 10px;
  line-height: 1;
  color: #fff;
}

.modal-warning {
  background: rgba(255, 107, 107, 0.15);
  border: 1px solid rgba(255, 107, 107, 0.3);
  border-radius: 6px;
  padding: 12px;
  margin-top: 16px;
  font-size: 13px;
  line-height: 1.5;
}

.modal-close {
  display: block;
  width: 100%;
  margin-top: 20px;
  padding: 12px;
  background: #4ecdc4;
  color: #1a1a2e;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
}

.modal-close:hover {
  background: #3dbdb5;
}
</style>
