#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::System {
class String;
}

namespace DotNet::System::Runtime::InteropServices {

class Marshal {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  public: Marshal() = delete;
  private: static void* (*CallStringToCoTaskMemUTF8_ga80EVd9gqZ4YlhSP8iRzg)(void* s, void** reinteropException);
  public: static void* StringToCoTaskMemUTF8(const ::DotNet::System::String& s);
  private: static void (*CallFreeCoTaskMem_eF5IwSJe_WM3IuDxcegQFg)(void* ptr, void** reinteropException);
  public: static void FreeCoTaskMem(void* ptr);
};

} // namespace DotNet::System::Runtime::InteropServices


