#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::System {
class Object;
}

namespace DotNet::Reinterop {

class ObjectHandleUtility {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  public: ObjectHandleUtility() = delete;
  private: static void* (*CallCreateHandle_vjOnn8y5DjvqKs3467vAJQ)(void* o, void** reinteropException);
  public: static void* CreateHandle(const ::DotNet::System::Object& o);
  private: static void* (*CallCopyHandle_Lk0gUmdC13dRVZ_MAT71eg)(void* handle, void** reinteropException);
  public: static void* CopyHandle(void* handle);
  private: static void (*CallFreeHandle_Lk0gUmdC13dRVZ_MAT71eg)(void* handle, void** reinteropException);
  public: static void FreeHandle(void* handle);
};

} // namespace DotNet::Reinterop


