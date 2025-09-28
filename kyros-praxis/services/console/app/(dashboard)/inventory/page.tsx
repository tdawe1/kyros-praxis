'use client';

import { 
  Button, 
  Tile, 
  Layer,
  InlineNotification,
  DataTable,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  Tag,
  Search,
} from '@carbon/react';
import { ShoppingCart, Add, Package, WarningAlt } from '@carbon/icons-react';

export default function InventoryPage() {
  // Mock inventory data
  const inventoryItems = [
    {
      id: '1',
      sku: 'PROD-001',
      name: 'Widget Pro Max',
      stock: 145,
      reserved: 12,
      reorderPoint: 50,
      status: 'in_stock',
      location: 'Warehouse A',
    },
    {
      id: '2',
      sku: 'PROD-002',
      name: 'Gadget Ultra',
      stock: 23,
      reserved: 5,
      reorderPoint: 30,
      status: 'low_stock',
      location: 'Warehouse B',
    },
    {
      id: '3',
      sku: 'PROD-003',
      name: 'Tool Deluxe',
      stock: 0,
      reserved: 0,
      reorderPoint: 20,
      status: 'out_of_stock',
      location: 'Warehouse A',
    },
  ];

  const headers = [
    { key: 'sku', header: 'SKU' },
    { key: 'name', header: 'Product Name' },
    { key: 'stock', header: 'In Stock' },
    { key: 'reserved', header: 'Reserved' },
    { key: 'reorderPoint', header: 'Reorder Point' },
    { key: 'status', header: 'Status' },
    { key: 'location', header: 'Location' },
  ];

  const statusConfig = {
    in_stock: { type: 'green', label: 'In Stock' },
    low_stock: { type: 'magenta', label: 'Low Stock' },
    out_of_stock: { type: 'red', label: 'Out of Stock' },
  } as const;

  return (
    <div className="cds--content">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ marginBottom: '0.5rem' }}>Inventory Management</h1>
        <p style={{ color: 'var(--cds-text-secondary)' }}>
          Track product stock levels and manage inventory
        </p>
      </div>

      <InlineNotification
        kind="warning"
        title="Low Stock Alert"
        subtitle="3 products are below reorder threshold"
        hideCloseButton
        lowContrast
        style={{ marginBottom: '2rem' }}
      />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <Layer>
          <Tile>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
              <Package size={20} style={{ marginRight: '0.5rem' }} />
              <span style={{ color: 'var(--cds-text-secondary)' }}>Total Products</span>
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>247</div>
            <Tag type="green" size="sm">+12% this month</Tag>
          </Tile>
        </Layer>

        <Layer>
          <Tile>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
              <ShoppingCart size={20} style={{ marginRight: '0.5rem' }} />
              <span style={{ color: 'var(--cds-text-secondary)' }}>Total Stock Value</span>
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>$45,230</div>
            <Tag type="blue" size="sm">Updated today</Tag>
          </Tile>
        </Layer>

        <Layer>
          <Tile>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
              <WarningAlt size={20} style={{ marginRight: '0.5rem', color: 'var(--cds-support-warning)' }} />
              <span style={{ color: 'var(--cds-text-secondary)' }}>Low Stock Items</span>
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>8</div>
            <Tag type="magenta" size="sm">Needs attention</Tag>
          </Tile>
        </Layer>

        <Layer>
          <Tile>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
              <Package size={20} style={{ marginRight: '0.5rem' }} />
              <span style={{ color: 'var(--cds-text-secondary)' }}>Pending Orders</span>
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>34</div>
            <Tag type="gray" size="sm">Processing</Tag>
          </Tile>
        </Layer>
      </div>

      <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem' }}>
        <Search
          size="lg"
          placeholder="Search inventory..."
          labelText="Search"
          closeButtonLabelText="Clear search input"
          style={{ flex: 1, maxWidth: '400px' }}
        />
        <Button renderIcon={Add} kind="primary">
          Add Product
        </Button>
        <Button kind="tertiary">
          Import CSV
        </Button>
      </div>

      <DataTable
        rows={inventoryItems}
        headers={headers}
        render={({
          rows,
          headers,
          getHeaderProps,
          getRowProps,
          getTableProps,
        }) => (
          <TableContainer title="Product Inventory">
            <Table {...getTableProps()}>
              <TableHead>
                <TableRow>
                  {headers.map((header) => {
                    const { key, ...headerProps } = getHeaderProps({ header });
                    return (
                      <TableHeader key={header.key} {...headerProps}>
                        {header.header}
                      </TableHeader>
                    );
                  })}
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.map((row) => {
                  const { key, ...rowProps } = getRowProps({ row });
                  return (
                    <TableRow key={row.id} {...rowProps}>
                    {row.cells.map((cell) => {
                      if (cell.info.header === 'status') {
                        const status = cell.value as keyof typeof statusConfig;
                        return (
                          <TableCell key={cell.id}>
                            <Tag type={statusConfig[status].type}>
                              {statusConfig[status].label}
                            </Tag>
                          </TableCell>
                        );
                      }
                      if (cell.info.header === 'stock') {
                        const stockLevel = cell.value as number;
                        const reorderPoint = row.cells.find(c => c.info.header === 'reorderPoint')?.value as number;
                        return (
                          <TableCell key={cell.id}>
                            <span style={{
                              color: stockLevel === 0 ? 'var(--cds-support-error)' :
                                     stockLevel < reorderPoint ? 'var(--cds-support-warning)' : 
                                     'inherit'
                            }}>
                              {cell.value}
                            </span>
                          </TableCell>
                        );
                      }
                      return <TableCell key={cell.id}>{cell.value}</TableCell>;
                    })}
                  </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      />
    </div>
  );
}