#pragma once





namespace DotNet::Reinterop {

class ObjectHandle {
public:
  ObjectHandle() noexcept;
  explicit ObjectHandle(void* handle) noexcept;
  ObjectHandle(const ObjectHandle& rhs) noexcept;
  ObjectHandle(ObjectHandle&& rhs) noexcept;
  ~ObjectHandle() noexcept;

  ObjectHandle& operator=(const ObjectHandle& rhs) noexcept;
  ObjectHandle& operator=(ObjectHandle&& rhs) noexcept;

  void* GetRaw() const;

  // Return the underlying raw handle and set the object's to nullptr
  // so it will not be released when this object is destroyed.
  void* Release();

private:
  void* _handle;
};

} // namespace DotNet::Reinterop


