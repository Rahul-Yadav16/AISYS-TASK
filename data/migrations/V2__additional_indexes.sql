-- V2__additional_indexes.sql
-- Optimizes query performance across high-volume circulation, search, and gate event tables

CREATE INDEX IF NOT EXISTS idx_items_accession ON items(accession_number);
CREATE INDEX IF NOT EXISTS idx_items_barcode ON items(barcode);
CREATE INDEX IF NOT EXISTS idx_items_biblio ON items(biblio_id);
CREATE INDEX IF NOT EXISTS idx_rfid_tags_uid ON rfid_tags(tag_uid);
CREATE INDEX IF NOT EXISTS idx_circ_member_status ON circulation_transactions(member_id, status);
CREATE INDEX IF NOT EXISTS idx_circ_item_status ON circulation_transactions(item_id, status);
CREATE INDEX IF NOT EXISTS idx_gate_events_time ON gate_security_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_members_card ON members(smart_card_uid);
CREATE INDEX IF NOT EXISTS idx_users_card ON users(smart_card_uid);

INSERT OR IGNORE INTO schema_migrations (version) VALUES ('V2__additional_indexes');
