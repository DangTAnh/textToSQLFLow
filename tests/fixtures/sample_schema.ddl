CREATE TABLE invoice (
    invoice_id    STRING    NOT NULL    COMMENT 'Mã hóa đơn',
    customer_id   STRING    NOT NULL    COMMENT 'Mã khách hàng',
    amount        DECIMAL(18,2) NOT NULL COMMENT 'Số tiền',
    invoice_date  DATE      NOT NULL    COMMENT 'Ngày hóa đơn',
    status        STRING                COMMENT 'Trạng thái',
    PRIMARY KEY (invoice_id)
)
PARTITIONED BY (invoice_date);

CREATE TABLE customer (
    customer_id   STRING    NOT NULL    COMMENT 'Mã khách hàng',
    name          STRING    NOT NULL    COMMENT 'Tên khách hàng',
    segment       STRING                COMMENT 'Phân khúc',
    PRIMARY KEY (customer_id)
);
