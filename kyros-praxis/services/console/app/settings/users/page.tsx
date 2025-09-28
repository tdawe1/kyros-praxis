'use client';

import { useState, useEffect } from 'react';
import {
  DataTable,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  Button,
  Modal,
  TextInput,
  Select,
  SelectItem,
  Loading,
  InlineNotification,
  Tag,
  Tile,
} from '@carbon/react';
import { Add, Edit } from '@carbon/icons-react';
import { RoleGuard } from '../../../components/rbac/PermissionGuards';
import { useUserRole } from '../../../lib/hooks/useUserRole';
import { UserRole, User } from '../../../lib/rbac';

interface UserWithActions extends User {
  actions?: React.ReactNode;
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [notification, setNotification] = useState<{
    type: 'success' | 'error' | 'info';
    message: string;
  } | null>(null);
  
  const { role: currentUserRole } = useUserRole();

  // Mock data - in a real app this would come from an API
  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setUsers([
        {
          id: '1',
          username: 'admin@example.com',
          email: 'admin@example.com',
          role: 'admin',
          active: true,
          created_at: '2024-01-01T00:00:00Z',
        },
        {
          id: '2',
          username: 'editor@example.com', 
          email: 'editor@example.com',
          role: 'editor',
          active: true,
          created_at: '2024-01-02T00:00:00Z',
        },
        {
          id: '3',
          username: 'viewer@example.com',
          email: 'viewer@example.com', 
          role: 'viewer',
          active: true,
          created_at: '2024-01-03T00:00:00Z',
        },
        {
          id: '4',
          username: 'integrator@example.com',
          email: 'integrator@example.com',
          role: 'integrator', 
          active: false,
          created_at: '2024-01-04T00:00:00Z',
        },
      ]);
      setLoading(false);
    }, 1000);
  }, []);

  const handleEditUser = (user: User) => {
    setEditingUser(user);
    setIsModalOpen(true);
  };

  const handleSaveUser = async (userData: Partial<User>) => {
    try {
      // In a real app, this would be an API call
      if (editingUser) {
        setUsers(prev => prev.map(u => 
          u.id === editingUser.id ? { ...u, ...userData } : u
        ));
        setNotification({
          type: 'success',
          message: `User ${userData.email || editingUser.email} updated successfully`
        });
      }
      setIsModalOpen(false);
      setEditingUser(null);
    } catch (error) {
      setNotification({
        type: 'error',
        message: 'Failed to update user'
      });
    }
  };

  const getRoleColor = (role: UserRole) => {
    switch (role) {
      case 'admin': return 'red';
      case 'editor': return 'blue';
      case 'integrator': return 'purple';
      case 'viewer': 
      default: return 'gray';
    }
  };

  const headers = [
    { key: 'username', header: 'Username' },
    { key: 'email', header: 'Email' },
    { key: 'role', header: 'Role' },
    { key: 'active', header: 'Status' },
    { key: 'created_at', header: 'Created' },
    { key: 'actions', header: 'Actions' },
  ];

  const tableData: UserWithActions[] = users.map(user => ({
    ...user,
    role: (
      <Tag type={getRoleColor(user.role)}>
        {user.role}
      </Tag>
    ),
    active: user.active ? 'Active' : 'Inactive',
    created_at: new Date(user.created_at).toLocaleDateString(),
    actions: (
      <RoleGuard allowedRoles={['admin']}>
        <Button
          kind="ghost"
          size="sm"
          renderIcon={Edit}
          onClick={() => handleEditUser(user)}
        >
          Edit
        </Button>
      </RoleGuard>
    ),
  }));

  if (loading) {
    return <Loading />;
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold mb-2">Users & Roles</h1>
          <p className="text-gray-600">
            Manage user accounts and role assignments for the system.
          </p>
        </div>
        
        <RoleGuard allowedRoles={['admin']} fallback={null}>
          <Button
            renderIcon={Add}
            onClick={() => {
              setEditingUser(null);
              setIsModalOpen(true);
            }}
          >
            Add User
          </Button>
        </RoleGuard>
      </div>

      {notification && (
        <div className="mb-4">
          <InlineNotification
            kind={notification.type}
            title={notification.message}
            onCloseButtonClick={() => setNotification(null)}
            hideCloseButton={false}
          />
        </div>
      )}

      {/* Role Information Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Tile>
          <h3 className="font-semibold mb-2">Viewer</h3>
          <p className="text-sm text-gray-600">
            Read-only access to most features. Can view agents, jobs, and system information.
          </p>
        </Tile>
        <Tile>
          <h3 className="font-semibold mb-2">Editor</h3>
          <p className="text-sm text-gray-600">
            Can create and edit agents, jobs, and tasks. Inherits viewer permissions.
          </p>
        </Tile>
        <Tile>
          <h3 className="font-semibold mb-2">Integrator</h3>
          <p className="text-sm text-gray-600">
            Special API-focused role with read/write access to most resources.
          </p>
        </Tile>
        <Tile>
          <h3 className="font-semibold mb-2">Admin</h3>
          <p className="text-sm text-gray-600">
            Full system access including user management and system administration.
          </p>
        </Tile>
      </div>

      <RoleGuard 
        allowedRoles={['admin', 'editor']} 
        fallback={
          <InlineNotification
            kind="info"
            title="Restricted Access"
            subtitle="You don't have permission to view the user list. Contact an administrator for access."
          />
        }
      >
        <DataTable rows={tableData} headers={headers}>
          {({ rows, headers, getHeaderProps, getRowProps, getTableProps }) => (
            <Table {...getTableProps()}>
              <TableHead>
                <TableRow>
                  {headers.map((header) => (
                    <TableHeader {...getHeaderProps({ header })} key={header.key}>
                      {header.header}
                    </TableHeader>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.map((row) => (
                  <TableRow {...getRowProps({ row })} key={row.id}>
                    {row.cells.map((cell) => (
                      <TableCell key={cell.id}>
                        {cell.value}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </DataTable>
      </RoleGuard>

      <UserEditModal
        isOpen={isModalOpen}
        user={editingUser}
        onClose={() => {
          setIsModalOpen(false);
          setEditingUser(null);
        }}
        onSave={handleSaveUser}
      />
    </div>
  );
}

interface UserEditModalProps {
  isOpen: boolean;
  user: User | null;
  onClose: () => void;
  onSave: (userData: Partial<User>) => void;
}

function UserEditModal({ isOpen, user, onClose, onSave }: UserEditModalProps) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    role: 'viewer' as UserRole,
    active: true,
  });

  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username,
        email: user.email,
        role: user.role,
        active: user.active,
      });
    } else {
      setFormData({
        username: '',
        email: '',
        role: 'viewer',
        active: true,
      });
    }
  }, [user]);

  const handleSubmit = () => {
    onSave(formData);
  };

  return (
    <Modal
      open={isOpen}
      modalHeading={user ? 'Edit User' : 'Add User'}
      modalLabel="User Management"
      primaryButtonText="Save"
      secondaryButtonText="Cancel"
      onRequestClose={onClose}
      onRequestSubmit={handleSubmit}
    >
      <div className="space-y-4">
        <TextInput
          id="username"
          labelText="Username"
          value={formData.username}
          onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
          required
        />
        <TextInput
          id="email"
          labelText="Email"
          type="email"
          value={formData.email}
          onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
          required
        />
        <Select
          id="role"
          labelText="Role"
          value={formData.role}
          onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value as UserRole }))}
        >
          <SelectItem value="viewer" text="Viewer" />
          <SelectItem value="editor" text="Editor" />
          <SelectItem value="integrator" text="Integrator" />
          <SelectItem value="admin" text="Admin" />
        </Select>
        <Select
          id="active"
          labelText="Status"
          value={formData.active ? 'active' : 'inactive'}
          onChange={(e) => setFormData(prev => ({ ...prev, active: e.target.value === 'active' }))}
        >
          <SelectItem value="active" text="Active" />
          <SelectItem value="inactive" text="Inactive" />
        </Select>
      </div>
    </Modal>
  );
}