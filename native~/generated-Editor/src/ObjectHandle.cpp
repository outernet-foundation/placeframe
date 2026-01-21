#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ObjectHandleUtility.h>



namespace DotNet::Reinterop {

ObjectHandle::ObjectHandle() noexcept : _handle(nullptr) {}

ObjectHandle::ObjectHandle(void* handle) noexcept : _handle(handle) {}

ObjectHandle::ObjectHandle(const ObjectHandle& rhs) noexcept
    : _handle(ObjectHandleUtility::CopyHandle(rhs._handle)) {}

ObjectHandle::ObjectHandle(ObjectHandle&& rhs) noexcept : _handle(rhs._handle) {
  rhs._handle = nullptr;
}

ObjectHandle::~ObjectHandle() noexcept {
  if (this->_handle != nullptr) {
    ObjectHandleUtility::FreeHandle(this->_handle);
  }
}

ObjectHandle& ObjectHandle::operator=(const ObjectHandle& rhs) noexcept {
  if (&rhs != this) {
    if (this->_handle != nullptr) {
      ObjectHandleUtility::FreeHandle(this->_handle);
    }
    this->_handle = ObjectHandleUtility::CopyHandle(rhs._handle);
  }

  return *this;
}

ObjectHandle& ObjectHandle::operator=(ObjectHandle&& rhs) noexcept {
  if (&rhs != this) {
    if (this->_handle != nullptr) {
      ObjectHandleUtility::FreeHandle(this->_handle);
    }
    this->_handle = rhs._handle;
    rhs._handle = nullptr;
  }

  return *this;
}

void* ObjectHandle::GetRaw() const { return this->_handle; }

void* ObjectHandle::Release() {
  void* handle = this->_handle;
  this->_handle = nullptr;
  return handle;
}

} // namespace DotNet::Reinterop


