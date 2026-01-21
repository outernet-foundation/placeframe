#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::UnityEngine {
struct Rect;
}

namespace DotNet::UnityEngine {

struct Rect {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_SWzoP__nNh7g2zNwjI5mUvQ)(float x, float y, float width, float height, ::DotNet::UnityEngine::Rect* pReturnValue, void** reinteropException);
  public: static Rect Construct(float x, float y, float width, float height);
  private: float m_XMin;
  private: float m_YMin;
  private: float m_Width;
  private: float m_Height;
};

} // namespace DotNet::UnityEngine


