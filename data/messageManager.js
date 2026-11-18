const fs = require('fs');
const path = require('path');

class MessageManager {
  constructor(dataDir = __dirname) {
    this.dataDir = dataDir;
    this.indexPath = path.join(dataDir, 'messages.json');
    this.messagesDir = path.join(dataDir, 'messages');
    this.index = JSON.parse(fs.readFileSync(this.indexPath, 'utf8'));
  }

  getAllMessages() {
    return this.index.messages;
  }

  // Get full message by ID
  getMessage(msgId) {
    const msgPath = path.join(this.messagesDir, `${msgId}.json`);
    return JSON.parse(fs.readFileSync(msgPath, 'utf8'));
  }

  addMessage(msgData) {
    const msgId = msgData.id;
    const msgPath = path.join(this.messagesDir, `${msgId}.json`);

    fs.writeFileSync(msgPath, JSON.stringify(msgData, null, 2));

    this.index.messages.push({
      id: msgId,
      file: `messages/${msgId}.json`,
      subject: msgData.subject,
      participants: msgData.participants,
      date: msgData.date,
      threadLength: msgData.thread.length,
      hasImages: msgData.thread.some(msg => msg.image)
    });

    this.saveIndex();
    return msgId;
  }
  addToThread(msgId, newMessages) {
    const msg = this.getMessage(msgId);
    msg.thread.push(...newMessages);

    const msgPath = path.join(this.messagesDir, `${msgId}.json`);
    fs.writeFileSync(msgPath, JSON.stringify(msg, null, 2));
    const indexEntry = this.index.messages.find(m => m.id === msgId);
    if (indexEntry) {
      indexEntry.threadLength = msg.thread.length;
      indexEntry.hasImages = msg.thread.some(m => m.image);
    }
    this.saveIndex();
  }

  // Attach image to message
  attachImage(msgId, imagePath) {
    const msg = this.getMessage(msgId);
    if (msg.thread.length === 0) throw new Error('Message has no thread');

    msg.thread[msg.thread.length - 1].image = imagePath;

    const msgPath = path.join(this.messagesDir, `${msgId}.json`);
    fs.writeFileSync(msgPath, JSON.stringify(msg, null, 2));
    const indexEntry = this.index.messages.find(m => m.id === msgId);
    if (indexEntry) indexEntry.hasImages = true;
    this.saveIndex();
  }
  saveIndex() {
    this.index.lastModified = new Date().toISOString();
    fs.writeFileSync(this.indexPath, JSON.stringify(this.index, null, 2));
  }
}

module.exports = MessageManager;
